package fixtures;

// Production code: a deliberate backoff delay, not a test — out of scope for this rule.
public class Production {

    public void backoff() throws InterruptedException {
        Thread.sleep(1000);
    }
}
