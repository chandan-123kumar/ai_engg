import java.util.LinkedList;

public class LinkedListRaceCondition {

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Without mutex (UNSAFE) ===");
        runTest(false);

        System.out.println("\n=== With mutex (SAFE) ===");
        runTest(true);
    }

    static void runTest(boolean useMutex) throws InterruptedException {
        LinkedList<Integer> list = new LinkedList<>();
        Object lock = new Object();
        int itemsPerThread = 1000;
        int threadCount = 10;

        Thread[] threads = new Thread[threadCount];

        for (int t = 0; t < threadCount; t++) {
            threads[t] = new Thread(() -> {
                for (int i = 0; i < itemsPerThread; i++) {
                    try {
                        if (useMutex) {
                            synchronized (lock) {
                                list.add(i);
                            }
                        } else {
                            list.add(i); // race condition here
                        }
                    } catch (Exception e) {
                        // ConcurrentModificationException or NullPointerException
                        // can crash here without mutex
                        System.out.println("  CRASH during add: " + e.getClass().getSimpleName());
                    }
                }
            });
        }

        for (Thread t : threads) t.start();
        for (Thread t : threads) t.join();

        int expected = threadCount * itemsPerThread;
        int actual = list.size();

        System.out.println("  Expected size : " + expected);
        System.out.println("  Actual size   : " + actual);

        if (actual != expected) {
            System.out.println("  DATA LOST: " + (expected - actual) + " items missing due to race condition!");
        } else {
            System.out.println("  All items accounted for.");
        }
    }
}
