package coordination.leader_election;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class Raft {
    enum State { LEADER, FOLLOWER, CANDIDATE }

    private State currentState;
    private final int nodeId;
    private final int totalNodes;
    private int currentTerm;
    private int votedFor;
    private final List<Integer> log;
    private final Map<Integer, Integer> nextIndex;
    private final Map<Integer, Integer> matchIndex;
    private int commitIndex;
    private int lastApplied;
    private final Lock lock = new ReentrantLock();
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    
    private final Map<Integer, Boolean> votesReceived = new ConcurrentHashMap<>();
    private final Random random = new Random();
    private boolean electionTimeout = false;

    public Raft(int nodeId, int totalNodes) {
        this.nodeId = nodeId;
        this.totalNodes = totalNodes;
        this.currentState = State.FOLLOWER;
        this.currentTerm = 0;
        this.votedFor = -1;
        this.log = new ArrayList<>();
        this.nextIndex = new HashMap<>();
        this.matchIndex = new HashMap<>();
        this.commitIndex = 0;
        this.lastApplied = 0;
        startElectionTimeout();
    }

    private void startElectionTimeout() {
        scheduler.schedule(() -> {
            lock.lock();
            try {
                if (!electionTimeout) {
                    becomeCandidate();
                }
            } finally {
                lock.unlock();
            }
        }, 150 + random.nextInt(150), TimeUnit.MILLISECONDS);
    }

    private void becomeFollower(int term) {
        lock.lock();
        try {
            currentState = State.FOLLOWER;
            currentTerm = term;
            votedFor = -1;
            startElectionTimeout();
        } finally {
            lock.unlock();
        }
    }

    private void becomeCandidate() {
        lock.lock();
        try {
            currentState = State.CANDIDATE;
            currentTerm++;
            votedFor = nodeId;
            votesReceived.clear();
            votesReceived.put(nodeId, true);
            requestVotes();
        } finally {
            lock.unlock();
        }
    }

    private void becomeLeader() {
        lock.lock();
        try {
            currentState = State.LEADER;
            for (int i = 0; i < totalNodes; i++) {
                nextIndex.put(i, log.size());
                matchIndex.put(i, 0);
            }
            sendHeartbeats();
        } finally {
            lock.unlock();
        }
    }

    private void requestVotes() {
        for (int i = 0; i < totalNodes; i++) {
            if (i != nodeId) {
                sendVoteRequest(i);
            }
        }
    }

    private void sendVoteRequest(int node) {
        // Simulating sending vote request to another node
        System.out.println("Node " + nodeId + " requesting vote from node " + node);
        scheduler.schedule(() -> receiveVoteResponse(node, true), random.nextInt(100), TimeUnit.MILLISECONDS);
    }

    private void receiveVoteResponse(int node, boolean voteGranted) {
        lock.lock();
        try {
            if (currentState == State.CANDIDATE && voteGranted) {
                votesReceived.put(node, true);
                if (votesReceived.size() > totalNodes / 2) {
                    becomeLeader();
                }
            }
        } finally {
            lock.unlock();
        }
    }

    private void sendHeartbeats() {
        scheduler.scheduleAtFixedRate(() -> {
            lock.lock();
            try {
                if (currentState == State.LEADER) {
                    for (int i = 0; i < totalNodes; i++) {
                        if (i != nodeId) {
                            sendAppendEntries(i);
                        }
                    }
                }
            } finally {
                lock.unlock();
            }
        }, 0, 100, TimeUnit.MILLISECONDS);
    }

    private void sendAppendEntries(int node) {
        // Simulating sending append entries (heartbeat) to another node
        System.out.println("Node " + nodeId + " sending heartbeat to node " + node);
        scheduler.schedule(() -> receiveAppendEntriesResponse(node, true), random.nextInt(100), TimeUnit.MILLISECONDS);
    }

    private void receiveAppendEntriesResponse(int node, boolean success) {
        lock.lock();
        try {
            if (currentState == State.LEADER && success) {
                nextIndex.put(node, log.size());
                matchIndex.put(node, log.size() - 1);
                updateCommitIndex();
            }
        } finally {
            lock.unlock();
        }
    }

    private void updateCommitIndex() {
        for (int i = log.size() - 1; i > commitIndex; i--) {
            int matchCount = 0;
            for (int node : matchIndex.values()) {
                if (node >= i) {
                    matchCount++;
                }
            }
            if (matchCount > totalNodes / 2 && log.get(i) == currentTerm) {
                commitIndex = i;
                applyEntries();
                break;
            }
        }
    }

    private void applyEntries() {
        while (lastApplied < commitIndex) {
            lastApplied++;
            // Simulating applying log entry to state machine
            System.out.println("Node " + nodeId + " applying log entry " + log.get(lastApplied));
        }
    }

    public void receiveAppendEntries(int term, int leaderId, int prevLogIndex, int prevLogTerm, List<Integer> entries, int leaderCommit) {
        lock.lock();
        try {
            if (term < currentTerm) {
                return; // Reply false if term < currentTerm
            }
            becomeFollower(term);
            if (log.size() - 1 < prevLogIndex || log.get(prevLogIndex) != prevLogTerm) {
                return; // Reply false if log doesn't contain an entry at prevLogIndex whose term matches prevLogTerm
            }
            log.addAll(entries); // Append any new entries not already in the log
            if (leaderCommit > commitIndex) {
                commitIndex = Math.min(leaderCommit, log.size() - 1);
                applyEntries();
            }
        } finally {
            lock.unlock();
        }
    }

    public void receiveVoteRequest(int term, int candidateId, int lastLogIndex, int lastLogTerm) {
        lock.lock();
        try {
            if (term > currentTerm) {
                becomeFollower(term);
            }
            if ((votedFor == -1 || votedFor == candidateId) && lastLogIndex >= log.size() - 1 && lastLogTerm >= currentTerm) {
                votedFor = candidateId;
                sendVoteResponse(candidateId, true);
            } else {
                sendVoteResponse(candidateId, false);
            }
        } finally {
            lock.unlock();
        }
    }

    private void sendVoteResponse(int candidateId, boolean voteGranted) {
        // Simulating sending vote response to another node
        System.out.println("Node " + nodeId + " sending vote response to node " + candidateId + ": " + (voteGranted ? "granted" : "denied"));
    }

    public static void main(String[] args) {
        Raft raft = new Raft(0, 5);
        raft.receiveVoteRequest(1, 2, 0, 1);  
        raft.receiveAppendEntries(1, 1, 0, 1, Arrays.asList(1, 2, 3), 1); 
    }
}