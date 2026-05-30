public class Main {
    public static void main(String[] args) throws InterruptedException {
        MySemaphore semaphore = new MySemaphore(1);

        Thread threadA = new Thread(() -> work(semaphore), "Thread-A");
        Thread threadB = new Thread(() -> work(semaphore), "Thread-B");

        threadA.start();
        threadB.start();

        threadA.join();
        threadB.join();

        System.out.println("Done.");
    }

    static void work(MySemaphore semaphore) {
        try {
            semaphore.acquire();
            System.out.println(Thread.currentThread().getName() + " working");
            Thread.sleep(500);
            semaphore.release();
            System.out.println(Thread.currentThread().getName() + " done");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
