package fixtures;

// Credentials baked straight into the source tree.
public class Bad {

    private static final String apiKey = "sk-live-1a2b3c4d";

    public String connect() {
        String password = "hunter2pass";
        return apiKey + ":" + password;
    }
}
