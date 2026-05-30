// system_grinding/semaphore/MySemaphore.java
import java.util.LinkedList;

public class MySemaphore {
    private int permits;
    private final LinkedList<Thread> waitQueue = new LinkedList<>();

    public MySemaphore(int permits) {
        if (permits < 0) throw new IllegalArgumentException("permits must be >= 0");
        this.permits = permits;
    }

    public synchronized void acquire() throws InterruptedException {
        Thread current = Thread.currentThread();
        waitQueue.addLast(current);

        while (permits == 0 || waitQueue.peek() != current) {
            wait();
        }

        waitQueue.poll();
        permits--;
    }

    public synchronized void release() {
        permits++;
        notifyAll();
    }
}
