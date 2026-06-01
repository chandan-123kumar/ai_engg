import java.util.LinkedList;

public class MyBlockingQueue<T> {
    private final MySemaphore emptySlots;
    private final MySemaphore filledSlots;
    private final MyMutex mutex;
    private final LinkedList<T> queue;

    public MyBlockingQueue(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be > 0");
        this.emptySlots = new MySemaphore(capacity);
        this.filledSlots = new MySemaphore(0);
        this.mutex = new MyMutex();
        this.queue = new LinkedList<>();
    }

    public void put(T item) throws InterruptedException {
        emptySlots.acquire();
        mutex.lock();
        queue.add(item);
        mutex.unlock();
        filledSlots.release();
    }

    public T take() throws InterruptedException {
        filledSlots.acquire();
        mutex.lock();
        T item = queue.poll();
        mutex.unlock();
        emptySlots.release();
        return item;
    }

    public int size() {
        return queue.size();
    }
}
