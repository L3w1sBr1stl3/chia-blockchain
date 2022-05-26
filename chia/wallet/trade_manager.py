import dataclasses
import logging
import time
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from chia.protocols.wallet_protocol import CoinState
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.spend_bundle import SpendBundle
from chia.util.db_wrapper import DBWrapper
from chia.util.hash import std_hash
from chia.util.ints import uint32, uint64
from chia.wallet.payment import Payment
from chia.wallet.puzzle_drivers import PuzzleInfo, Solver
from chia.wallet.trade_record import TradeRecord
from chia.wallet.trading.offer import NotarizedPayment, Offer
from chia.wallet.trading.trade_status import TradeStatus
from chia.wallet.trading.trade_store import TradeStore
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.util.transaction_type import TransactionType
from chia.wallet.util.wallet_types import WalletType
from chia.wallet.wallet import Wallet
from chia.wallet.wallet_coin_record import WalletCoinRecord


class TradeManager:
    """
    This class is a driver for creating and accepting settlement_payments.clvm style offers.

    By default, standard XCH is supported but to support other types of assets you must implement certain functions on
    the asset's wallet as well as create a driver for its puzzle(s).  Here is a guide to integrating a new types of
    assets with this trade manager:

    Puzzle Drivers:
      - See chia/wallet/outer_puzzles.py for a full description of how to build these
      - The `solve` method must be able to be solved by a Solver that looks like this:
            Solver(
                {
                    "coin": bytes
                    "parent_spend": bytes
                    "siblings": List[bytes]  # other coins of the same type being offered
                    "sibling_spends": List[bytes]  # The parent spends for the siblings
                    "sibling_puzzles": List[Program]  # The inner puzzles of the siblings (always OFFER_MOD)
                    "sibling_solutions": List[Program]  # The inner solution of the siblings
                }
            )

    Wallet:
      - Segments in this code that call general wallet methods are highlighted by comments: # ATTENTION: new wallets
      - To be able to be traded, a wallet must implement these methods on itself:
        - generate_signed_transaction(...) -> List[TransactionRecord]  (See cat_wallet.py for full API)
        - convert_puzzle_hash(puzzle_hash: bytes32) -> bytes32  # Converts a puzzlehash from outer to inner puzzle
        - get_puzzle_info(asset_id: bytes32) -> PuzzleInfo
        - get_coins_to_offer(asset_id: bytes32, amount: uint64) -> Set[Coin]
      - If you would like assets from your wallet to be referenced with just a wallet ID, you must also implement:
        - get_asset_id() -> bytes32
      - Finally, you must make sure that your wallet will respond appropriately when these WSM methods are called:
        - get_wallet_for_puzzle_info(puzzle_info: PuzzleInfo) -> <Your wallet>
        - create_wallet_for_puzzle_info(puzzle_info: PuzzleInfo) -> <Your wallet>
        - get_wallet_for_asset_id(asset_id: bytes32) -> <Your wallet>
    """

    wallet_state_manager: Any
    log: logging.Logger
    trade_store: TradeStore

    @staticmethod
    async def create(
        wallet_state_manager: Any,
        db_wrapper: DBWrapper,
        name: str = None,
    ):
        self = TradeManager()
        if name:
            self.log = logging.getLogger(name)
        else:
            self.log = logging.getLogger(__name__)

        self.wallet_state_manager = wallet_state_manager
        self.trade_store = await TradeStore.create(db_wrapper)
        return self

    async def get_offers_with_status(self, status: TradeStatus) -> List[TradeRecord]:
        records = await self.trade_store.get_trade_record_with_status(status)
        return records

    async def get_coins_of_interest(
        self,
    ) -> Dict[bytes32, Coin]:
        """
        Returns list of coins we want to check if they are included in filter,
        These will include coins that belong to us and coins that that on other side of treade
        """
        all_pending = []
        pending_accept = await self.get_offers_with_status(TradeStatus.PENDING_ACCEPT)
        pending_confirm = await self.get_offers_with_status(TradeStatus.PENDING_CONFIRM)
        pending_cancel = await self.get_offers_with_status(TradeStatus.PENDING_CANCEL)
        all_pending.extend(pending_accept)
        all_pending.extend(pending_confirm)
        all_pending.extend(pending_cancel)
        interested_dict = {}

        for trade in all_pending:
            for coin in trade.coins_of_interest:
                interested_dict[coin.name()] = coin

        return interested_dict

    async def get_trade_by_coin(self, coin: Coin) -> Optional[TradeRecord]:
        all_trades = await self.get_all_trades()
        for trade in all_trades:
            if trade.status == TradeStatus.CANCELLED.value:
                continue
            if coin in trade.coins_of_interest:
                return trade
        return None

    async def coins_of_interest_farmed(self, coin_state: CoinState, fork_height: Optional[uint32]):
        """
        If both our coins and other coins in trade got removed that means that trade was successfully executed
        If coins from other side of trade got farmed without ours, that means that trade failed because either someone
        else completed trade or other side of trade canceled the trade by doing a spend.
        If our coins got farmed but coins from other side didn't, we successfully canceled trade by spending inputs.
        """
        self.log.info(f"coins_of_interest_farmed: {coin_state}")
        trade = await self.get_trade_by_coin(coin_state.coin)
        if trade is None:
            self.log.error(f"Coin: {coin_state.coin}, not in any trade")
            return
        if coin_state.spent_height is None:
            self.log.error(f"Coin: {coin_state.coin}, has not been spent so trade can remain valid")

        # Then let's filter the offer into coins that WE offered
        offer = Offer.from_bytes(trade.offer)
        primary_coin_ids = [c.name() for c in offer.get_primary_coins()]
        our_coin_records: List[WalletCoinRecord] = await self.wallet_state_manager.coin_store.get_multiple_coin_records(
            primary_coin_ids
        )
        our_primary_coins: List[bytes32] = [cr.coin.name() for cr in our_coin_records]
        all_settlement_payments: List[Coin] = [c for coins in offer.get_offered_coins().values() for c in coins]
        our_settlement_payments: List[Coin] = list(
            filter(lambda c: offer.get_root_removal(c).name() in our_primary_coins, all_settlement_payments)
        )
        our_settlement_ids: List[bytes32] = [c.name() for c in our_settlement_payments]

        # And get all relevant coin states
        coin_states = await self.wallet_state_manager.wallet_node.get_coin_state(our_settlement_ids, fork_height)
        assert coin_states is not None
        coin_state_names: List[bytes32] = [cs.coin.name() for cs in coin_states]

        # If any of our settlement_payments were spent, this offer was a success!
        if set(our_settlement_ids) & set(coin_state_names):
            height = coin_states[0].spent_height
            await self.trade_store.set_status(trade.trade_id, TradeStatus.CONFIRMED, True, height)
            tx_records: List[TransactionRecord] = await self.calculate_tx_records_for_offer(offer, False)
            for tx in tx_records:
                if TradeStatus(trade.status) == TradeStatus.PENDING_ACCEPT:
                    await self.wallet_state_manager.add_transaction(
                        dataclasses.replace(tx, confirmed_at_height=height, confirmed=True), in_transaction=True
                    )

            self.log.info(f"Trade with id: {trade.trade_id} confirmed at height: {height}")
        else:
            # In any other scenario this trade failed
            await self.wallet_state_manager.delete_trade_transactions(trade.trade_id)
            if trade.status == TradeStatus.PENDING_CANCEL.value:
                await self.trade_store.set_status(trade.trade_id, TradeStatus.CANCELLED, True)
                self.log.info(f"Trade with id: {trade.trade_id} canceled")
            elif trade.status == TradeStatus.PENDING_CONFIRM.value:
                await self.trade_store.set_status(trade.trade_id, TradeStatus.FAILED, True)
                self.log.warning(f"Trade with id: {trade.trade_id} failed")

    async def get_locked_coins(self, wallet_id: int = None) -> Dict[bytes32, WalletCoinRecord]:
        """Returns a dictionary of confirmed coins that are locked by a trade."""
        all_pending = []
        pending_accept = await self.get_offers_with_status(TradeStatus.PENDING_ACCEPT)
        pending_confirm = await self.get_offers_with_status(TradeStatus.PENDING_CONFIRM)
        pending_cancel = await self.get_offers_with_status(TradeStatus.PENDING_CANCEL)
        all_pending.extend(pending_accept)
        all_pending.extend(pending_confirm)
        all_pending.extend(pending_cancel)

        coins_of_interest = []
        for trade_offer in all_pending:
            coins_of_interest.extend([c.name() for c in Offer.from_bytes(trade_offer.offer).get_involved_coins()])

        result = {}
        coin_records = await self.wallet_state_manager.coin_store.get_multiple_coin_records(coins_of_interest)
        for record in coin_records:
            if wallet_id is None or record.wallet_id == wallet_id:
                result[record.name()] = record

        return result

    async def get_all_trades(self):
        all: List[TradeRecord] = await self.trade_store.get_all_trades()
        return all

    async def get_trade_by_id(self, trade_id: bytes32) -> Optional[TradeRecord]:
        record = await self.trade_store.get_trade_record(trade_id)
        return record

    async def cancel_pending_offer(self, trade_id: bytes32):
        await self.trade_store.set_status(trade_id, TradeStatus.CANCELLED, False)
        self.wallet_state_manager.state_changed("offer_cancelled")

    async def cancel_pending_offer_safely(
        self, trade_id: bytes32, fee: uint64 = uint64(0)
    ) -> Optional[List[TransactionRecord]]:
        """This will create a transaction that includes coins that were offered"""
        self.log.info(f"Secure-Cancel pending offer with id trade_id {trade_id.hex()}")
        trade = await self.trade_store.get_trade_record(trade_id)
        if trade is None:
            return None

        all_txs: List[TransactionRecord] = []
        fee_to_pay: uint64 = fee
        for coin in Offer.from_bytes(trade.offer).get_primary_coins():
            wallet = await self.wallet_state_manager.get_wallet_for_coin(coin.name())

            if wallet is None:
                continue
            new_ph = await wallet.get_new_puzzlehash()
            # This should probably not switch on whether or not we're spending an XCH but it has to for now
            # ATTENTION: new_wallets
            if wallet.type() == WalletType.STANDARD_WALLET:
                if fee_to_pay > coin.amount:
                    selected_coins: Set[Coin] = await wallet.select_coins(
                        uint64(fee_to_pay - coin.amount),
                        exclude=[coin],
                    )
                    selected_coins.add(coin)
                else:
                    selected_coins = {coin}
                tx = await wallet.generate_signed_transaction(
                    uint64(sum([c.amount for c in selected_coins]) - fee_to_pay),
                    new_ph,
                    fee=fee_to_pay,
                    coins=selected_coins,
                    ignore_max_send_amount=True,
                )
                all_txs.append(tx)
            else:
                txs = await wallet.generate_signed_transaction(
                    [coin.amount], [new_ph], fee=fee_to_pay, coins={coin}, ignore_max_send_amount=True
                )
                all_txs.extend(txs)
            fee_to_pay = uint64(0)

            cancellation_addition = Coin(coin.name(), new_ph, coin.amount)
            all_txs.append(
                TransactionRecord(
                    confirmed_at_height=uint32(0),
                    created_at_time=uint64(int(time.time())),
                    to_puzzle_hash=new_ph,
                    amount=coin.amount,
                    fee_amount=fee,
                    confirmed=False,
                    sent=uint32(10),
                    spend_bundle=None,
                    additions=[cancellation_addition],
                    removals=[coin],
                    wallet_id=wallet.id(),
                    sent_to=[],
                    trade_id=None,
                    type=uint32(TransactionType.INCOMING_TX.value),
                    name=cancellation_addition.name(),
                    memos=[],
                )
            )

        for tx in all_txs:
            await self.wallet_state_manager.add_pending_transaction(tx_record=dataclasses.replace(tx, fee_amount=fee))

        await self.trade_store.set_status(trade_id, TradeStatus.PENDING_CANCEL, False)

        return all_txs

    async def save_trade(self, trade: TradeRecord):
        await self.trade_store.add_trade_record(trade, False)
        self.wallet_state_manager.state_changed("offer_added")

    async def create_offer_for_ids(
        self,
        offer: Dict[Union[int, bytes32], Union[Solver, int]],
        driver_dict: Optional[Dict[bytes32, PuzzleInfo]] = None,
        fee: uint64 = uint64(0),
        validate_only: bool = False,
    ) -> Tuple[bool, Optional[TradeRecord], Optional[str]]:
        if driver_dict is None:
            driver_dict = {}
        success, created_offer, error = await self._create_offer_for_ids(offer, driver_dict, fee=fee)
        if not success or created_offer is None:
            raise Exception(f"Error creating offer: {error}")

        now = uint64(int(time.time()))
        trade_offer: TradeRecord = TradeRecord(
            confirmed_at_index=uint32(0),
            accepted_at_time=None,
            created_at_time=now,
            is_my_offer=True,
            sent=uint32(0),
            offer=bytes(created_offer),
            taken_offer=None,
            coins_of_interest=created_offer.get_involved_coins(),
            trade_id=created_offer.name(),
            status=uint32(TradeStatus.PENDING_ACCEPT.value),
            sent_to=[],
        )

        if success is True and trade_offer is not None and not validate_only:
            await self.save_trade(trade_offer)

        return success, trade_offer, error

    async def _create_offer_for_ids(
        self,
        offer_dict: Dict[Union[int, bytes32], Union[Solver, int]],
        driver_dict: Optional[Dict[bytes32, PuzzleInfo]] = None,
        fee: uint64 = uint64(0),
    ) -> Tuple[bool, Optional[Offer], Optional[str]]:
        """
        Offer is dictionary of wallet ids and amounts/Solvers
        """
        if driver_dict is None:
            driver_dict = {}
        try:
            coins_to_offer: Dict[Union[int, bytes32], List[Coin]] = {}
            requested_payments: Dict[Optional[bytes32], List[Payment]] = {}
            fee_left_to_pay: uint64 = fee
            wallet_paying_fee: Union[int, bytes32]
            for id, solver in offer_dict.items():
                if isinstance(solver, int) & (solver > 0):  # type: ignore
                    if isinstance(id, int):
                        wallet_id = uint32(id)
                        wallet = self.wallet_state_manager.wallets[wallet_id]
                        p2_ph: bytes32 = await wallet.get_new_puzzlehash()
                        if wallet.type() == WalletType.STANDARD_WALLET:
                            asset_id: Optional[bytes32] = None
                            memos: List[bytes] = []
                        elif callable(getattr(wallet, "get_asset_id", None)):  # ATTENTION: new wallets
                            asset_id = bytes32(bytes.fromhex(wallet.get_asset_id()))
                            memos = [p2_ph]
                        else:
                            raise ValueError(
                                f"Cannot request assets from wallet id {wallet.id()} without more information"
                            )
                    else:
                        p2_ph = await self.wallet_state_manager.main_wallet.get_new_puzzlehash()
                        asset_id = id
                        wallet = await self.wallet_state_manager.get_wallet_for_asset_id(asset_id.hex())
                        memos = [p2_ph]
                    requested_payments[asset_id] = [Payment(p2_ph, uint64(solver), memos)]  # type: ignore
                else:
                    if isinstance(id, int):
                        wallet_id = uint32(id)
                        wallet = self.wallet_state_manager.wallets[wallet_id]
                        if wallet.type() == WalletType.STANDARD_WALLET:
                            asset_id = None
                        elif callable(getattr(wallet, "get_asset_id", None)):  # ATTENTION: new wallets
                            asset_id = bytes32(bytes.fromhex(wallet.get_asset_id()))
                        else:
                            raise ValueError(
                                f"Cannot offer assets from wallet id {wallet.id()} without more information"
                            )
                    else:
                        asset_id = id
                        wallet = await self.wallet_state_manager.get_wallet_for_asset_id(asset_id.hex())
                    if isinstance(solver, int):
                        if solver == 0:
                            raise ValueError("You cannot offer nor request 0 amount of something")
                        solver = uint64(abs(solver))
                    if not callable(getattr(wallet, "get_coins_to_offer", None)):  # ATTENTION: new wallets
                        raise ValueError(f"Cannot offer coins from wallet id {wallet.id()}")
                    coins_to_offer[id] = await wallet.get_coins_to_offer(asset_id, solver, fee_left_to_pay)
                    fee_left_to_pay = uint64(0)
                    wallet_paying_fee = id

                if asset_id is not None and wallet is not None:
                    if callable(getattr(wallet, "get_puzzle_info", None)):
                        puzzle_driver: PuzzleInfo = wallet.get_puzzle_info(asset_id)
                        if asset_id in driver_dict and driver_dict[asset_id] != puzzle_driver:
                            raise ValueError(
                                f"driver_dict specified {driver_dict[asset_id]}, was expecting {puzzle_driver}"
                            )
                        else:
                            driver_dict[asset_id] = puzzle_driver
                    else:
                        raise ValueError(f"Wallet for asset id {asset_id} is not properly integrated with TradeManager")

            all_coins: List[Coin] = [c for coins in coins_to_offer.values() for c in coins]
            notarized_payments: Dict[Optional[bytes32], List[NotarizedPayment]] = Offer.notarize_payments(
                requested_payments, all_coins
            )
            announcements_to_assert = Offer.calculate_announcements(notarized_payments, driver_dict)

            all_transactions: List[TransactionRecord] = []
            for id, selected_coins in coins_to_offer.items():
                if isinstance(id, int):
                    wallet = self.wallet_state_manager.wallets[id]
                else:
                    wallet = await self.wallet_state_manager.get_wallet_for_asset_id(id.hex())

                solver = offer_dict[id]
                if isinstance(solver, int):
                    solver = abs(solver)

                # ATTENTION: new_wallets
                this_fee: uint64 = fee if id == wallet_paying_fee else uint64(0)
                txs: List[TransactionRecord] = await wallet.create_offer_transactions(
                    solver, selected_coins, announcements_to_assert, this_fee
                )
                all_transactions.extend(txs)

            transaction_bundles: List[Optional[SpendBundle]] = [tx.spend_bundle for tx in all_transactions]
            total_spend_bundle = SpendBundle.aggregate(list(filter(lambda b: b is not None, transaction_bundles)))
            offer = Offer(notarized_payments, total_spend_bundle, driver_dict)
            return True, offer, None

        except Exception as e:
            tb = traceback.format_exc()
            self.log.error(f"Error with creating trade offer: {type(e)}{tb}")
            return False, None, str(e)

    async def maybe_create_wallets_for_offer(self, offer: Offer):

        for key in offer.arbitrage():
            wsm = self.wallet_state_manager
            if key is None:
                continue
            # ATTENTION: new_wallets
            exists: Optional[Wallet] = await wsm.get_wallet_for_puzzle_info(offer.driver_dict[key])
            if exists is None:
                await wsm.create_wallet_for_puzzle_info(offer.driver_dict[key])

    async def check_offer_validity(self, offer: Offer) -> bool:
        all_removals: List[Coin] = offer.bundle.removals()
        all_removal_names: List[bytes32] = [c.name() for c in all_removals]
        non_ephemeral_removals: List[Coin] = list(
            filter(lambda c: c.parent_coin_info not in all_removal_names, all_removals)
        )
        coin_states = await self.wallet_state_manager.wallet_node.get_coin_state(
            [c.name() for c in non_ephemeral_removals]
        )
        return len(coin_states) == len(non_ephemeral_removals) and all([cs.spent_height is None for cs in coin_states])

    async def calculate_tx_records_for_offer(self, offer: Offer, validate: bool) -> List[TransactionRecord]:
        if validate:
            final_spend_bundle: SpendBundle = offer.to_valid_spend()
        else:
            final_spend_bundle = offer.bundle

        settlement_coins: List[Coin] = [c for coins in offer.get_offered_coins().values() for c in coins]
        settlement_coin_ids: List[bytes32] = [c.name() for c in settlement_coins]
        additions: List[Coin] = final_spend_bundle.not_ephemeral_additions()
        removals: List[Coin] = final_spend_bundle.removals()
        all_fees = uint64(final_spend_bundle.fees())

        txs = []

        addition_dict: Dict[uint32, List[Coin]] = {}
        for addition in additions:
            wallet_info = await self.wallet_state_manager.get_wallet_id_for_puzzle_hash(addition.puzzle_hash)
            if wallet_info is not None:
                wallet_id, _ = wallet_info
                if addition.parent_coin_info in settlement_coin_ids:
                    wallet = self.wallet_state_manager.wallets[wallet_id]
                    to_puzzle_hash = await wallet.convert_puzzle_hash(addition.puzzle_hash)  # ATTENTION: new wallets
                    txs.append(
                        TransactionRecord(
                            confirmed_at_height=uint32(0),
                            created_at_time=uint64(int(time.time())),
                            to_puzzle_hash=to_puzzle_hash,
                            amount=addition.amount,
                            fee_amount=uint64(0),
                            confirmed=False,
                            sent=uint32(10),
                            spend_bundle=None,
                            additions=[addition],
                            removals=[],
                            wallet_id=wallet_id,
                            sent_to=[],
                            trade_id=offer.name(),
                            type=uint32(TransactionType.INCOMING_TRADE.value),
                            name=std_hash(final_spend_bundle.name() + addition.name()),
                            memos=[],
                        )
                    )
                else:  # This is change
                    addition_dict.setdefault(wallet_id, [])
                    addition_dict[wallet_id].append(addition)

        # While we want additions to show up as separate records, removals of the same wallet should show as one
        removal_dict: Dict[uint32, List[Coin]] = {}
        for removal in removals:
            wallet_info = await self.wallet_state_manager.get_wallet_id_for_puzzle_hash(removal.puzzle_hash)
            if wallet_info is not None:
                wallet_id, _ = wallet_info
                removal_dict.setdefault(wallet_id, [])
                removal_dict[wallet_id].append(removal)

        for wid, grouped_removals in removal_dict.items():
            wallet = self.wallet_state_manager.wallets[wid]
            to_puzzle_hash = bytes32([1] * 32)  # We use all zeros to be clear not to send here
            removal_tree_hash = Program.to([rem.as_list() for rem in grouped_removals]).get_tree_hash()
            # We also need to calculate the sent amount
            removed: int = sum(c.amount for c in grouped_removals)
            change_coins: List[Coin] = addition_dict[wid] if wid in addition_dict else []
            change_amount: int = sum(c.amount for c in change_coins)
            sent_amount: int = removed - change_amount
            txs.append(
                TransactionRecord(
                    confirmed_at_height=uint32(0),
                    created_at_time=uint64(int(time.time())),
                    to_puzzle_hash=to_puzzle_hash,
                    amount=uint64(sent_amount),
                    fee_amount=all_fees,
                    confirmed=False,
                    sent=uint32(10),
                    spend_bundle=None,
                    additions=change_coins,
                    removals=grouped_removals,
                    wallet_id=wallet.id(),
                    sent_to=[],
                    trade_id=offer.name(),
                    type=uint32(TransactionType.OUTGOING_TRADE.value),
                    name=std_hash(final_spend_bundle.name() + removal_tree_hash),
                    memos=[],
                )
            )

        return txs

    async def respond_to_offer(self, offer: Offer, fee=uint64(0)) -> Tuple[bool, Optional[TradeRecord], Optional[str]]:
        take_offer_dict: Dict[Union[bytes32, int], Union[Solver, int]] = {}
        arbitrage: Dict[Optional[bytes32], int] = offer.arbitrage()
        for asset_id, amount in arbitrage.items():
            if asset_id is None:
                wallet = self.wallet_state_manager.main_wallet
                key: Union[bytes32, int] = int(wallet.id())
            else:
                # ATTENTION: new wallets
                wallet = await self.wallet_state_manager.get_wallet_for_asset_id(asset_id.hex())
                if wallet is None and amount < 0:
                    return False, None, f"Do not have a wallet for asset ID: {asset_id} to fulfill offer"
                else:
                    key = asset_id
            take_offer_dict[key] = amount

        # First we validate that all of the coins in this offer exist
        valid: bool = await self.check_offer_validity(offer)
        if not valid:
            return False, None, "This offer is no longer valid"

        success, take_offer, error = await self._create_offer_for_ids(take_offer_dict, offer.driver_dict, fee=fee)
        if not success or take_offer is None:
            return False, None, error

        complete_offer = Offer.aggregate([offer, take_offer])
        assert complete_offer.is_valid()
        final_spend_bundle: SpendBundle = complete_offer.to_valid_spend()

        await self.maybe_create_wallets_for_offer(complete_offer)

        tx_records: List[TransactionRecord] = await self.calculate_tx_records_for_offer(complete_offer, True)

        trade_record: TradeRecord = TradeRecord(
            confirmed_at_index=uint32(0),
            accepted_at_time=uint64(int(time.time())),
            created_at_time=uint64(int(time.time())),
            is_my_offer=False,
            sent=uint32(0),
            offer=bytes(complete_offer),
            taken_offer=bytes(offer),
            coins_of_interest=complete_offer.get_involved_coins(),
            trade_id=complete_offer.name(),
            status=uint32(TradeStatus.PENDING_CONFIRM.value),
            sent_to=[],
        )

        await self.save_trade(trade_record)

        # Dummy transaction for the sake of the wallet push
        push_tx = TransactionRecord(
            confirmed_at_height=uint32(0),
            created_at_time=uint64(int(time.time())),
            to_puzzle_hash=bytes32([1] * 32),
            amount=uint64(0),
            fee_amount=uint64(0),
            confirmed=False,
            sent=uint32(0),
            spend_bundle=final_spend_bundle,
            additions=[],
            removals=[],
            wallet_id=uint32(0),
            sent_to=[],
            trade_id=bytes32([1] * 32),
            type=uint32(TransactionType.OUTGOING_TRADE.value),
            name=final_spend_bundle.name(),
            memos=[],
        )
        await self.wallet_state_manager.add_pending_transaction(push_tx)
        for tx in tx_records:
            await self.wallet_state_manager.add_transaction(tx)

        return True, trade_record, None
