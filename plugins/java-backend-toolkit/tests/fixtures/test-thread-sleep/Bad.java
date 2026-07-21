package fixtures;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

// Waits a fixed delay and hopes the work finished by then.
class Bad {

    @Test
    void processesAsync() throws InterruptedException {
        jobRunner.submit();
        Thread.sleep(1000);
        assertThat(jobRunner.isDone()).isTrue();
    }
}
