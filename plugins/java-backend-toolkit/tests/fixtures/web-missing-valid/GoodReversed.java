package fixtures;

import jakarta.validation.Valid;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

// Annotation order on a parameter is irrelevant to Spring: @RequestBody @Valid is
// equally valid and must stay clean (regression for the reversed-order false positive).
@RestController
public class GoodReversed {

    @PostMapping("/accounts")
    public AccountResponse create(@RequestBody @Valid CreateAccountRequest request) {
        return accountService.create(request);
    }
}
