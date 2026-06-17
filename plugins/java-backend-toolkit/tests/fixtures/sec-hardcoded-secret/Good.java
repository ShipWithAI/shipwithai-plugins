package fixtures;

// Secrets are injected, never literal: env var, empty default, config placeholder.
public class Good {

    private final String apiKey = System.getenv("API_KEY");

    public String connect() {
        String password = "";
        String fallback = "${DB_PASSWORD}";
        // Non-secret identifiers that must stay silent (regression for the bare "token"
        // keyword removal and the 8-char minimum):
        String csrfToken = "X-CSRF-Token";   // header name, "csrf*" is not a secret keyword
        String authToken = "Bearer";          // matches auth-token but only 6 chars (< 8)
        String pageToken = "dXNlcjE=";        // base64 pagination cursor, not a secret
        return apiKey + password + fallback + csrfToken + authToken + pageToken;
    }
}
