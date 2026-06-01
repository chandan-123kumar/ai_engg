public class Main {
    public static void main(String[] args) throws InterruptedException {
        MyMutex mutex = new MyMutex();

        Thread threadA = new Thread(() -> work(mutex), "Thread-A");
        Thread threadB = new Thread(() -> work(mutex), "Thread-B");
        Thread threadC = new Thread(() -> work1(mutex), "Thread-C");

        threadA.start();
        threadB.start();
        threadC.start();

        threadA.join();
        threadB.join();
        threadC.join();

        System.out.println("Done.");
    }
    
    static void work1(MyMutex mutex) {
        try {
            mutex.printer();
        } catch (Exception e) {
            Thread.currentThread().interrupt();
        }
    }
    static void work(MyMutex mutex) {
        try {
            mutex.lock();
            System.out.println(Thread.currentThread().getName() + " acquired lock");
            Thread.sleep(500);
            mutex.unlock();
            System.out.println(Thread.currentThread().getName() + " released lock");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
