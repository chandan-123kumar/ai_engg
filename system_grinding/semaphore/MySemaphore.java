
public class MySemaphore {
    private int permits;

    public MySemaphore(int permits) {
        if (permits < 0) throw new IllegalArgumentException("permits must be >= 0");
        this.permits = permits;
    }

    public synchronized void acquire() throws InterruptedException {
        while (permits == 0) {
            wait();
        }
        permits--;
    }

    public synchronized void release() {
        permits++;
        notifyAll();
    }

}
