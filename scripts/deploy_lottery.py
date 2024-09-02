import time
from brownie import (
    network,
    config,
    Lottery,
)
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account, get_contract

def deploy_lottery():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        account = get_account()
        lottery = Lottery.deploy(get_contract("eth_usd_price_feed"), get_contract("vrf_coordinator"), config["networks"][network.show_active()]["keyhash"], config["networks"][network.show_active()]["subscriptionId"], {"from":account})
    else:
        lottery = get_contract("lottery")
    print("Deployed Lottery")
    return lottery

def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    start_tx = lottery.startLottery({"from":account})
    start_tx.wait(1)
    print("Lottery has started!")

def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 100000000
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You entered the lottery!")

def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)

    # needed to make sure the coordinator has enough time to call the callback of the lottery contract
    time.sleep(180)

    print(f"{lottery.recentWinner()} is the new winner!")

def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()