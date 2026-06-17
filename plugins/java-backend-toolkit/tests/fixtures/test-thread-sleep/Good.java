package fixtures;

import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;

import java.time.Duration;

import org.junit.jupiter.api.Test;

// Polls for the expected state, returning as soon as it is reached.
class Good {

    @Test
    void processesAsync() {
        jobRunner.submit();
        await().atMost(Duration.ofSeconds(5))
                .untilAsserted(() -> assertThat(jobRunner.isDone()).isTrue());
    }
}
