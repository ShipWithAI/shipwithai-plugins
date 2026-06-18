package fixtures;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

// Handler that accepts a request payload but skips Bean Validation.
@RestController
public class Bad {

    @PostMapping("/accounts")
    public AccountResponse create(@RequestBody CreateAccountRequest request) {
        return accountService.create(request);
    }
}
