package fixtures;

import java.util.List;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Version;

// Standard DDD aggregate-root pattern: orphanRemoval=true with an explicit
// non-REMOVE cascade. This must stay clean — the rule flags only the full-cascade
// variant, never orphanRemoval on its own.
@Entity
public class GoodOrphanRemoval {

    @Id
    private Long id;

    @Version
    private Long version;

    @OneToMany(cascade = { CascadeType.PERSIST, CascadeType.MERGE }, orphanRemoval = true)
    private List<LineItem> items;
}
