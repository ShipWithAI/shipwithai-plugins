package fixtures;

// Secrets are injected, never literal: env var, empty default, config placeholder.
public class Good {

    private final String apiKey = System.getenv("API_KEY");

    public String connect() {
        String password = "";
        String fallback = "${DB_PASSWORD}";
        return apiKey + password + fallback;
    }
}
