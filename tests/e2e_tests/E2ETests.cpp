#include <iostream>
#include <string>
#include <cassert>
#include "../distributed/DistributedCache.cpp"
#include "../consistency/StrongConsistency.cpp"
#include "../replication/MasterSlaveReplication.cpp"

using namespace std;

class E2ETests {
public:
    static void runAllTests() {
        testPutOperation();
        testGetOperation();
        testDeleteOperation();
        testReplicationConsistency();
        testMasterSlaveFailover();
        testStrongConsistency();
    }

private:
    static void testPutOperation() {
        cout << "Running Put Operation Test..." << endl;

        DistributedCache cache;
        string key = "testKey";
        string value = "testValue";

        cache.put(key, value);
        string cachedValue = cache.get(key);

        assert(cachedValue == value);
        cout << "Put Operation Test Passed!" << endl;
    }

    static void testGetOperation() {
        cout << "Running Get Operation Test..." << endl;

        DistributedCache cache;
        string key = "testKey";
        string expectedValue = "testValue";

        string cachedValue = cache.get(key);

        assert(cachedValue == expectedValue);
        cout << "Get Operation Test Passed!" << endl;
    }

    static void testDeleteOperation() {
        cout << "Running Delete Operation Test..." << endl;

        DistributedCache cache;
        string key = "testKey";

        cache.put(key, "testValue");
        cache.remove(key);
        string cachedValue = cache.get(key);

        assert(cachedValue.empty());
        cout << "Delete Operation Test Passed!" << endl;
    }

    static void testReplicationConsistency() {
        cout << "Running Replication Consistency Test..." << endl;

        DistributedCache primaryCache;
        MasterSlaveReplication replication;
        
        string key = "replicationKey";
        string value = "replicationValue";

        // Simulate putting value in primary cache
        primaryCache.put(key, value);
        replication.replicate(primaryCache);

        // Simulate getting value from slave cache after replication
        DistributedCache slaveCache = replication.getSlaveCache();
        string replicatedValue = slaveCache.get(key);

        assert(replicatedValue == value);
        cout << "Replication Consistency Test Passed!" << endl;
    }

    static void testMasterSlaveFailover() {
        cout << "Running Master-Slave Failover Test..." << endl;

        MasterSlaveReplication replication;
        DistributedCache primaryCache;
        DistributedCache slaveCache;

        string key = "failoverKey";
        string value = "failoverValue";

        primaryCache.put(key, value);
        replication.replicate(primaryCache);

        // Simulate failure in master node
        replication.simulateMasterFailure();

        // Slave takes over as master
        DistributedCache newMasterCache = replication.promoteSlaveToMaster();

        string failoverValue = newMasterCache.get(key);
        assert(failoverValue == value);
        cout << "Master-Slave Failover Test Passed!" << endl;
    }

    static void testStrongConsistency() {
        cout << "Running Strong Consistency Test..." << endl;

        StrongConsistency strongConsistency;
        DistributedCache cache;

        string key1 = "consistentKey1";
        string value1 = "consistentValue1";

        string key2 = "consistentKey2";
        string value2 = "consistentValue2";

        // Put two values concurrently in the cache
        strongConsistency.putWithConsensus(cache, key1, value1);
        strongConsistency.putWithConsensus(cache, key2, value2);

        // Ensure both values are consistent across all nodes
        string cachedValue1 = cache.get(key1);
        string cachedValue2 = cache.get(key2);

        assert(cachedValue1 == value1);
        assert(cachedValue2 == value2);
        cout << "Strong Consistency Test Passed!" << endl;
    }
};

int main() {
    cout << "Starting End-to-End Tests..." << endl;
    E2ETests::runAllTests();
    cout << "All End-to-End Tests Passed!" << endl;
    return 0;
}