package fixtures;

import java.security.MessageDigest;

import org.apache.commons.codec.digest.DigestUtils;

// Hashing user passwords with a broken, fast digest.
public class Bad {

    public byte[] hashOne(String password) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("MD5");
        return digest.digest(password.getBytes());
    }

    public String hashTwo(String password) {
        return DigestUtils.sha1Hex(password);
    }
}
