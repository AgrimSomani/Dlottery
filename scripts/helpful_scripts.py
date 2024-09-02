from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    Contract,
    VRFCoordinatorV2_5Mock,
    Lottery
)

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
DECIMALS = 8
INITIAL_VALUE = 200000000000
BASEFEE = 100000000000000000
GASPRICELINK = 1000000000
WEIPERUNITLINK = 4356957406782896


def get_account(index=None, id=None):
    if id:
        return accounts[id]
    if index:
        return accounts[index]
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    account =  accounts.add(config["wallets"]["from_key"])
    print(f"Made account {account}")
    return account

contract_to_mock = {
    "eth_usd_price_feed":MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorV2_5Mock,
    "lottery":Lottery

}


def get_contract(contract_name):
    """
    Gets the address of the contract deployed from the config if not in development mode, or else deploy the mock contracts, and then return the contract object to work with
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) == 0:
            deploy_mock()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)
    
    return contract

def deploy_mock():
    account = get_account()
    MockV3Aggregator.deploy(DECIMALS, INITIAL_VALUE, {"from":account})
    VRFCoordinatorV2_5Mock.deploy(BASEFEE, GASPRICELINK, WEIPERUNITLINK ,{"from":account})
    print("Mocks deployed...")


    
