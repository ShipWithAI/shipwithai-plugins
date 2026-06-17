package fixtures;

import java.util.List;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Version;

@Entity
public class Good {

    @Id
    private Long id;

    @Version
    private Long version;

    @OneToMany(cascade = { CascadeType.PERSIST, CascadeType.MERGE })
    private List<LineItem> items;
}
