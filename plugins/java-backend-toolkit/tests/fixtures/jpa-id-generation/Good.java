package fixtures;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.SequenceGenerator;
import jakarta.persistence.Version;

@Entity
public class Good {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "good_seq")
    @SequenceGenerator(name = "good_seq", sequenceName = "good_seq", allocationSize = 50)
    private Long id;

    @Version
    private Long version;
}
