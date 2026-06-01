public class Main {
    static final int CAPACITY = 5;
    static final int ITEMS_PER_PRODUCER = 5;
    static final int NUM_PRODUCERS = 3;
    static final int NUM_CONSUMERS = 2;
    static final int POISON = 0;

    public static void main(String[] args) throws InterruptedException {
        MyBlockingQueue<Integer> queue = new MyBlockingQueue<>(CAPACITY);

        Thread[] producers = new Thread[NUM_PRODUCERS];
        Thread[] consumers = new Thread[NUM_CONSUMERS];

        for (int i = 0; i < NUM_PRODUCERS; i++) {
            final int producerId = i;
            producers[i] = new Thread(() -> {
                for (int j = 0; j < ITEMS_PER_PRODUCER; j++) {
                    try {
                        int item = producerId * ITEMS_PER_PRODUCER + j;
                        queue.put(item);
                        System.out.println(Thread.currentThread().getName() + " put " + item);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                }
            }, "Producer-" + i);
        }

        for (int i = 0; i < NUM_CONSUMERS; i++) {
            consumers[i] = new Thread(() -> {
                try {
                    while (true) {
                        Integer item = queue.take();
                        if (item == POISON) break;
                        System.out.println(Thread.currentThread().getName() + " took " + item);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "Consumer-" + i);
        }

        for (Thread c : consumers) c.start();
        for (Thread p : producers) p.start();

        for (Thread p : producers) p.join();

        for (int i = 0; i < NUM_CONSUMERS; i++) {
            queue.put(POISON);
        }

        for (Thread c : consumers) c.join();

        System.out.println("Done.");
    }
}
