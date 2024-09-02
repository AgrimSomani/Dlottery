// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import {AggregatorV3Interface} from "@chainlink/contracts/src/v0.8/shared/interfaces/AggregatorV3Interface.sol";
import {VRFConsumerBaseV2Plus} from "@chainlink/contracts/src/v0.8/vrf/dev/VRFConsumerBaseV2Plus.sol";
import {VRFV2PlusClient} from "@chainlink/contracts/src/v0.8/vrf/dev/libraries/VRFV2PlusClient.sol";

contract Lottery is VRFConsumerBaseV2Plus {
    address payable[] public players;
    uint256 public randomness;
    address payable public recentWinner;
    uint256 public usdEntryFee;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    AggregatorV3Interface internal ethUsdPriceFeed;
    LOTTERY_STATE public lotteryState;

    event RequestSent(uint256 requestId);

    // Your subscription ID.
    uint256 public s_subscriptionId;
    bytes32 public keyHash;
    uint32 public callbackGasLimit = 100000;
    uint16 public requestConfirmations = 3;
    uint32 public numWords = 1;

    constructor(
        address _priceFeedAddress,
        address _coordinatorAddress,
        bytes32 _keyhash,
        uint256 _s_subscriptionId
    ) VRFConsumerBaseV2Plus(_coordinatorAddress) {
        usdEntryFee = 50 * (10 ** 18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lotteryState = LOTTERY_STATE.CLOSED;
        keyHash = _keyhash;
        s_subscriptionId = _s_subscriptionId;
    }

    function enter() public payable {
        // $10 minimum
        require(lotteryState == LOTTERY_STATE.OPEN, "Lottery is not open yet");
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        players.push(payable(msg.sender));
    }

    function getEntranceFee() public view returns (uint256) {
        (
            ,
            /* uint80 roundID */ int answer /*uint startedAt*/ /*uint timeStamp*/ /*uint80 answeredInRound*/,
            ,
            ,

        ) = ethUsdPriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(answer) * 10 ** 10; //18 decimals in wei format
        uint256 res = (usdEntryFee * 10 ** 18) / adjustedPrice;
        return res;
    }

    function startLottery() public {
        require(
            lotteryState == LOTTERY_STATE.CLOSED,
            "Cant start a new lottery yet"
        );
        lotteryState = LOTTERY_STATE.OPEN;
    }

    function requestRandomWords(
        bool enableNativePayment
    ) internal onlyOwner returns (uint256 requestId) {
        // Will revert if subscription is not set and funded.
        requestId = s_vrfCoordinator.requestRandomWords(
            VRFV2PlusClient.RandomWordsRequest({
                keyHash: keyHash,
                subId: s_subscriptionId,
                requestConfirmations: requestConfirmations,
                callbackGasLimit: callbackGasLimit,
                numWords: numWords,
                extraArgs: VRFV2PlusClient._argsToBytes(
                    VRFV2PlusClient.ExtraArgsV1({
                        nativePayment: enableNativePayment
                    })
                )
            })
        );
        return requestId;
    }

    function endLottery() public onlyOwner {
        lotteryState = LOTTERY_STATE.CALCULATING_WINNER;
        uint256 requestId = requestRandomWords(false);
        emit RequestSent(requestId);
    }

    function fulfillRandomWords(
        uint256 _requestId,
        uint256[] calldata _randomWords
    ) internal override {
        require(
            lotteryState == LOTTERY_STATE.CALCULATING_WINNER,
            "You aren't there yet!"
        );
        uint256 _randomness = _randomWords[0];
        require(_randomness > 0, "random-not-found");
        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);

        // Reset
        players = new address payable[](0);
        lotteryState = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
