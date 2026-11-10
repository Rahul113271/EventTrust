// SPDX-License-Identifier: MIT
pragma solidity >= 0.8.11 <= 0.8.11;

/**
 * @title EventRegistry
 * @dev Decentralized Cryptographic Integrity, Multi-Witness Consensus,
 * and Trust Verification Layer for Intelligent Event Detection.
 */
contract Event {
    struct EventRecord {
        uint256 eventId;       // Unique ID mapping to Supabase public.events.id
        bytes32 dataHash;      // SHA-256 cryptographic digest of the event
        uint8 trustScore;      // Explainable Trust Score (0 to 100)
        uint256 timestamp;     // Block timestamp when anchored on Ethereum
        address recordedBy;    // Ethereum account that committed the record
        bool exists;           // O(1) existence verification flag
        uint16 confirmations;  // Multi-witness verification votes
        uint16 disputes;       // Community dispute flags
        uint8 status;          // 0 = Pending, 1 = Verified Consensus, 2 = Disputed, 3 = Tampered
    }

    // --- Access Control ---
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Unauthorized: caller is not the contract owner");
        _;
    }

    // --- Event Storage Mapping ---
    mapping(uint256 => EventRecord) public events;
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    uint256[] public eventIds;
    uint256 public totalEvents;

    // --- Latest Event Pointers (for fast lookups) ---
    uint256 public latestEventId;
    bytes32 public latestPostHash;
    uint256 public latestTrustScore;

    // --- User Storage (for backward compatibility with existing registration/login) ---
    string public users;

    // --- EVM Events for On-Chain Audit Logging ---
    event EventRecorded(
        uint256 indexed eventId,
        bytes32 indexed dataHash,
        uint8 trustScore,
        uint256 timestamp,
        address indexed recordedBy
    );

    event WitnessVoted(
        uint256 indexed eventId,
        address indexed voter,
        bool confirmsDisaster,
        uint16 confirmations,
        uint16 disputes
    );

    event EventTampered(
        uint256 indexed eventId,
        bytes32 tamperedHash,
        uint8 trustScore
    );

    event EventRestored(
        uint256 indexed eventId,
        bytes32 restoredHash,
        uint8 restoredTrustScore
    );

    constructor() {
        owner = msg.sender;
        totalEvents = 0;
        latestEventId = 0;
        latestTrustScore = 0;
        latestPostHash = bytes32(0);
        users = "";
    }

    // ============================================================
    // CORE EVENT REGISTRY FUNCTIONS
    // ============================================================

    /**
     * @notice Records a detected event's cryptographic proof and trust score on-chain.
     */
    function recordEvent(
        uint256 _eventId,
        bytes32 _dataHash,
        uint8 _trustScore
    ) external onlyOwner {
        require(_trustScore <= 100, "Trust score cannot exceed 100");
        require(!events[_eventId].exists, "Event ID already registered on blockchain");

        events[_eventId] = EventRecord({
            eventId: _eventId,
            dataHash: _dataHash,
            trustScore: _trustScore,
            timestamp: block.timestamp,
            recordedBy: msg.sender,
            exists: true,
            confirmations: 0, // Starts at 0 until independent multi-witnesses audit
            disputes: 0,
            status: 0         // 0 = Pending consensus audit
        });

        eventIds.push(_eventId);
        totalEvents++;

        latestEventId = _eventId;
        latestPostHash = _dataHash;
        latestTrustScore = _trustScore;

        emit EventRecorded(_eventId, _dataHash, _trustScore, block.timestamp, msg.sender);
    }

    /**
     * @notice Casts an independent witness / responder consensus vote on an event.
     */
    function castWitnessVote(uint256 _eventId, bool _confirmsDisaster) external {
        require(events[_eventId].exists, "Event ID not registered on blockchain");
        require(!hasVoted[_eventId][msg.sender], "Caller has already voted on this event");

        hasVoted[_eventId][msg.sender] = true;

        if (_confirmsDisaster) {
            events[_eventId].confirmations++;
            if (events[_eventId].trustScore <= 96) {
                events[_eventId].trustScore += 2;
            }
        } else {
            events[_eventId].disputes++;
            if (events[_eventId].trustScore >= 15) {
                events[_eventId].trustScore -= 15;
            } else {
                events[_eventId].trustScore = 0;
            }
        }

        if (events[_eventId].disputes > events[_eventId].confirmations) {
            events[_eventId].status = 2; // Disputed
        } else {
            events[_eventId].status = 1; // Verified Consensus
        }

        emit WitnessVoted(_eventId, msg.sender, _confirmsDisaster, events[_eventId].confirmations, events[_eventId].disputes);
    }

    /**
     * @notice Returns the decentralized multi-witness consensus state.
     */
    function getConsensusDetails(uint256 _eventId) external view returns (
        uint16 confirmations,
        uint16 disputes,
        uint8 status
    ) {
        require(events[_eventId].exists, "Event ID does not exist");
        return (events[_eventId].confirmations, events[_eventId].disputes, events[_eventId].status);
    }

    /**
     * @notice Retrieves full on-chain record for a specific event ID.
     */
    function getEvent(uint256 _eventId) external view returns (
        bytes32 dataHash,
        uint8 trustScore,
        uint256 timestamp,
        address recordedBy,
        bool exists
    ) {
        EventRecord memory rec = events[_eventId];
        return (rec.dataHash, rec.trustScore, rec.timestamp, rec.recordedBy, rec.exists);
    }

    /**
     * @notice Verifies an off-chain calculated SHA-256 hash directly against the blockchain proof.
     */
    function verifyEventHash(uint256 _eventId, bytes32 _testHash) external view returns (
        bool isMatch,
        uint8 score
    ) {
        if (!events[_eventId].exists) {
            return (false, 0);
        }
        bool matchFound = (events[_eventId].dataHash == _testHash);
        return (matchFound, matchFound ? events[_eventId].trustScore : 0);
    }

    /**
     * @notice Returns total number of events anchored on Ethereum.
     */
    function getEventCount() external view returns (uint256) {
        return totalEvents;
    }

    // ============================================================
    // CONTROLLED ACADEMIC DEMONSTRATION / TEST MODE
    // ============================================================

    /**
     * @notice DEMO / TEST MODE ONLY: Simulates data tampering on a specific event.
     */
    function simulateEventTampering(
        uint256 _eventId,
        bytes32 _tamperedHash
    ) external onlyOwner {
        require(events[_eventId].exists, "Event ID does not exist");

        events[_eventId].dataHash = _tamperedHash;
        events[_eventId].trustScore = 0;
        events[_eventId].status = 3; // Tampered

        if (_eventId == latestEventId) {
            latestPostHash = _tamperedHash;
            latestTrustScore = 0;
        }

        emit EventTampered(_eventId, _tamperedHash, 0);
    }

    /**
     * @notice DEMO / TEST MODE ONLY: Restores legitimate hash and authentic trust score.
     */
    function restoreEvent(
        uint256 _eventId,
        bytes32 _originalHash,
        uint8 _originalTrustScore
    ) external onlyOwner {
        require(events[_eventId].exists, "Event ID does not exist");
        require(_originalTrustScore <= 100, "Trust score cannot exceed 100");

        events[_eventId].dataHash = _originalHash;
        events[_eventId].trustScore = _originalTrustScore;
        events[_eventId].status = 1; // Restored

        if (_eventId == latestEventId) {
            latestPostHash = _originalHash;
            latestTrustScore = _originalTrustScore;
        }

        emit EventRestored(_eventId, _originalHash, _originalTrustScore);
    }

    // ============================================================
    // BACKWARD COMPATIBILITY WRAPPERS
    // ============================================================

    function addUser(string memory us) external onlyOwner {
        users = us;
    }

    function getUser() external view returns (string memory) {
        return users;
    }

    function getPost() external pure returns (string memory) {
        return "";
    }

    function getPostHash() external view returns (bytes32) {
        return latestPostHash;
    }

    function getTrustScore() external view returns (uint256) {
        return latestTrustScore;
    }
}
