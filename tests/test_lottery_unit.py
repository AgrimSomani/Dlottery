from web3 import Web3
import pytest
from brownie import network, exceptions
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account, get_contract

def test_get_entrance_fee():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    # 2000 eth/usd set in the mock contract
    # usdEntryFee is 10     
    expected_entrance_fee = Web3.to_wei(0.005, "ether")
    entrance_fee = lottery.getEntranceFee()
    assert expected_entrance_fee == entrance_fee

def test_cant_enter_unless_started():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter(
            {"from": get_account(), "value": lottery.getEntranceFee()}
        )

def test_can_start_and_enter_lottery():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery_contract = deploy_lottery()
    account = get_account()
    lottery_contract.startLottery({"from": account})
    # Act
    lottery_contract.enter(
        {"from": account, "value": lottery_contract.getEntranceFee()}
    )
    # Assert
    assert lottery_contract.players(0) == account

def test_can_pick_winner_correctly():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from":account})
    lottery.enter({"from":account, "value":lottery.getEntranceFee()})
    lottery.enter({"from":get_account(1), "value":lottery.getEntranceFee()})
    lottery.enter({"from":get_account(2), "value":lottery.getEntranceFee()}) 
    transaction = lottery.endLottery({"from":account})
    request_id = transaction.events["RequestSent"]["requestId"]
    MOCK_RANDOM = 666
    get_contract("vrf_coordinator").fulfillRandomWordsWithOverride(request_id, lottery.address, [MOCK_RANDOM], {"from":account})

    starting_balance_of_winner_account = account.balance()
    lottery_balance = lottery.balance()

    # 666%3 = 0
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_winner_account+lottery_balance
