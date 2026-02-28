"""LikeC4 DSL schema documentation module.

Single source of truth for the c4 format — used by the AI system prompt,
OpenAPI descriptions, and any tooling that needs to understand the DSL.

Grammar reference: packages/language-server/src/like-c4.langium
Examples reference: examples/cloud-system/
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Top-level file structure
# ---------------------------------------------------------------------------

_TOP_LEVEL = """
## Top-level blocks

A .c4 file may contain any combination of these top-level blocks (order does not matter):

  specification { ... }   – Define element kinds, relationship kinds, tags, colors, deployment node kinds
  model { ... }           – Declare elements (actors, systems, containers, etc.) and relations
  views { ... }           – Declare architecture views
  deployment { ... }      – Declare deployment nodes and deployed instances
  globals { ... }         – Shared style/predicate groups reused across views
  import { A, B } from 'project'  – Import elements from another project
  likec4lib { icons { ... } }     – Register custom icon sets
"""

# ---------------------------------------------------------------------------
# Specification block
# ---------------------------------------------------------------------------

_SPECIFICATION = """
## Specification block

Define element kinds, relationship kinds, tags, colors, and deployment node kinds.

```
specification {
  // Element kind with optional style and notation
  element actor {
    notation "Person"
    style {
      shape person
    }
  }
  element system {
    notation "Software System"
    style {
      opacity 10%
    }
  }
  element container {
    style { opacity 50% }
  }
  element component {
    style { opacity 50% }
  }

  // Deployment node kind
  deploymentNode cloud {
    style {
      icon aws:cloud
    }
  }

  // Named relationship kinds (for -[kind]-> syntax and dot notation)
  relationship uses
  relationship requests

  // Tags (referenced in elements/relations with #tag syntax)
  tag deprecated
  tag api

  // Custom named colors (hex)
  color custom #6BD731
}
```

Element style properties:
  shape: rectangle | person | browser | mobile | queue | storage | cylinder | hexagon | ellipse
  color: primary | secondary | muted | slate | blue | sky | indigo | green | amber | red | gray | <custom-color-name>
  icon: <icon-id>  (e.g. aws:lambda, tech:graphql, https://…/icon.svg)
  opacity: <0–100>%
  multiple: true | false
  size: xs | sm | md | lg | xl
  border: solid | dashed | dotted | none
"""

# ---------------------------------------------------------------------------
# Model block – elements
# ---------------------------------------------------------------------------

_MODEL_ELEMENTS = """
## Model block — elements

Elements are declared inside `model { ... }`.

Two equivalent syntaxes:
  id = kind 'Title' 'summary'?
  kind id 'Title' 'summary'?   (legacy Structurizr-like form)

Full element body:
```
model {
  // Simple element
  customer = actor 'Customer' 'End user of the system'

  // Element with full body
  cloud = system 'Cloud System' {
    // Tags (must be declared in specification first)
    #tag1, #tag2

    // String properties (any order, all optional)
    title 'Cloud System'
    description '''
      Multi-line **markdown** description.
      Supports GFM: tables, code blocks, admonitions.
    '''
    technology 'Python, FastAPI'

    // Link to external URL or file path
    link https://example.com 'Docs'
    link ./path/to/file.md#L10-L20 'Source'

    // Metadata key-value pairs (arbitrary strings)
    metadata {
      version '2.1.1'
      team    'platform'
      sla     ['99.9%', '24h']
    }

    // Nested child elements
    api = container 'API' 'REST API backend' {
      db = component 'Database' {
        style { shape storage }
      }
      -> db 'reads/writes'          // relation inside child body (source is implicit: api)
    }

    ui = container 'Frontend' {
      style { shape browser }
    }
  }

  // Stand-alone relation in model block
  customer -> cloud 'uses' 'REST' {
    navigateTo dynamic-view-1
  }
}
```

Element properties summary:
  title       — display name (overrides the positional string)
  description — markdown text (single-quoted or triple-quoted)
  technology  — technology/stack string
  summary     — short summary line
  link <url> '<label>'   — clickable external link
  metadata { key 'value' ... }
  style { <style-props> }
  icon <icon-id>
  #tag ...    — tag annotations (comma-separated after opening brace)
"""

# ---------------------------------------------------------------------------
# Model block – relations
# ---------------------------------------------------------------------------

_MODEL_RELATIONS = """
## Model block — relations

Relations connect elements. They can appear:
  • Inside `model { ... }` (must specify source)
  • Inside an element body `{ ... }` (source is implicit — the containing element)

Syntaxes:
  source -> target                    – simple relation
  source -> target 'label'            – with title
  source -> target 'label' 'desc' 'tech'  – with title, description, technology
  -> target 'label'                   – inside element body (source implicit)
  source -[kind]-> target 'label'     – typed relation (kind from specification)
  source .uses target 'label'         – dot notation (shorthand for -[uses]->)
  source .requests target             – dot notation

Relation body (all properties optional):
```
customer -> cloud 'uses' {
  #tag1, #tag2
  title 'Uses'
  description 'Customer browses the web UI'
  technology 'HTTPS'
  navigateTo dynamic-view-1    // jump to a dynamic view
  link https://docs.example.com 'API Docs'
  metadata {
    rps '1000'
  }
  style {
    color red
    line dashed
    head normal | none | open | diamond
    tail normal | none | open | diamond
  }
}
```

Extend an existing relation (add metadata, tags, or style without redeclaring):
```
extend source .uses target {
  #deprecated
  metadata { note 'will be removed' }
}
```
"""

# ---------------------------------------------------------------------------
# Extend element
# ---------------------------------------------------------------------------

_EXTEND_ELEMENT = """
## Extending elements

Add properties, relations, or children to elements defined elsewhere (another file):

```
extend cloud.api {
  #new-tag
  link https://docs.example.com 'OpenAPI'
  metadata { owner 'team-platform' }

  newChild = component 'New Child'
  -> cloud.ui 'notifies'
}
```
"""

# ---------------------------------------------------------------------------
# Views block
# ---------------------------------------------------------------------------

_VIEWS = """
## Views block

Views are declared inside `views { ... }`.

### Element view (static)
```
views {
  // Landscape view — no specific element
  view index {
    title 'System Landscape'
    description 'All elements and relations'
    include *
    autoLayout TopBottom
  }

  // View focused on a specific element
  view cloud of cloud {
    title 'Cloud System'
    include *           // all direct children + relations
    include cloud.*     // children of cloud
    exclude cloud.legacy
    exclude customer -> cloud  // exclude specific relation

    // Inline style override
    style cloud {
      color sky
    }
    style cloud.* {
      color primary
    }

    autoLayout LeftRight 150 80   // direction rankSep? nodeSep?
  }

  // Extend another view
  view extended extends cloud {
    include amazon
  }
}
```

autoLayout directions: TopBottom | LeftRight | BottomTop | RightLeft

### Dynamic view (sequence/flow)
```
views {
  dynamic view login-flow {
    title 'Login Flow'

    // Steps (numbered automatically, rendered as sequence)
    customer -> ui.login 'opens login page'
    ui.login -> api.auth 'POST /auth/login'
    api.auth -> db 'validates credentials'
    api.auth <- db 'returns token'
    ui.login <- api.auth 'JWT' {
      navigateTo dashboard-view
    }

    // Parallel steps
    parallel {
      api.auth -> audit.log 'records attempt'
      api.auth -> email 'sends confirmation'
    }

    // Backward arrow
    db <- api.auth 'query result'

    include cloud       // add context elements
    autoLayout TopBottom

    style * { size sm }
  }
}
```

### Deployment view
```
deployment {
  node prod 'Production' {
    node aws 'AWS' {
      node eks 'EKS Cluster' {
        instanceOf cloud.api
        instanceOf cloud.ui
      }
      node rds 'RDS' {
        instanceOf cloud.db
      }
    }
  }
}

views {
  deployment view prod-view of prod {
    title 'Production Deployment'
    include *
    autoLayout TopBottom
  }
}
```

### View predicates (include / exclude)
```
include *                  // all elements visible from scope
include element            // specific element
include element.*          // element and direct children
include element._          // element's descendants (deep)
include -> element         // element + all incoming relations
include element ->         // element + all outgoing relations
include element <-> element2  // both directions
include element -> element2   // specific relation
include element where tag is #api  // filtered by tag
include element where kind is container  // filtered by kind
```

### Inline style overrides within view
```
include cloud -> * with {
  color red
  line dashed
}
include customer with {
  color green
  icon tech:person
  navigateTo customer-view
}
```

### Groups
```
group 'SAAS' {
  color primary
  opacity 20%
  include cloud.*
}
group 'External' {
  color green
  border dashed
  include customer
}
```

### Rank (layout hints)
```
rank same { cloud.api, cloud.ui }
rank min   { customer }
```
"""

# ---------------------------------------------------------------------------
# Deployment block
# ---------------------------------------------------------------------------

_DEPLOYMENT = """
## Deployment block

Declares infrastructure and deployment topology.

```
deployment {
  node prod 'Production' {
    // Nested nodes
    node aws-region 'us-east-1' {
      node eks 'EKS Cluster' {
        // Deploy a logical model element instance
        instanceOf cloud.api
        instanceOf cloud.ui

        -> rds 'JDBC'
      }
      node rds 'RDS Aurora' {
        instanceOf cloud.db
      }
    }
  }
}
```
"""

# ---------------------------------------------------------------------------
# Globals block
# ---------------------------------------------------------------------------

_GLOBALS = """
## Globals block

Define reusable predicate groups and style groups that can be referenced in views.

```
globals {
  predicate group show-internals {
    include cloud.*
    exclude cloud.legacy
  }

  style group highlight-external {
    style customer { color green }
    style amazon   { color amber }
  }
}

views {
  view index {
    global predicate show-internals
    global style highlight-external
  }
}
```
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

_IMPORTS = """
## Imports

Import elements from another project (multi-project workspace):

```
import { cloud, customer } from 'backend-project'
import { amazon } from 'infra-project'
```

Imported elements can be referenced by ID in the current model.
"""

# ---------------------------------------------------------------------------
# Strings and comments
# ---------------------------------------------------------------------------

_STRINGS_AND_COMMENTS = """
## Strings

Single-quoted:  'Hello World'
Double-quoted:  "Hello World"
Triple-quoted (markdown):
  '''
  ## Heading
  Regular **bold** and _italic_ text.
  ```
  code block
  ```
  '''

Triple-quoted strings support GitHub Flavored Markdown including tables,
admonitions (> [!NOTE], > [!TIP], > [!WARNING], etc.), and code fences.

## Comments

  // Single-line comment
  /* Multi-line
     comment */
"""

# ---------------------------------------------------------------------------
# Style properties reference
# ---------------------------------------------------------------------------

_STYLE_PROPERTIES = """
## Style properties

Element styles (inside `style { ... }` blocks):
  shape:   rectangle | person | browser | mobile | queue | storage | cylinder | hexagon | ellipse
  color:   primary | secondary | muted | slate | blue | sky | indigo | green | amber | red | gray | <custom>
  icon:    <icon-id>  (e.g. aws:lambda, tech:graphql, none)
  opacity: <0–100>%
  size:    xs | sm | md | lg | xl
  multiple: true | false   (show stack/pile visual)
  border:  solid | dashed | dotted | none

Relation styles (inside relation `style { ... }` or view `style <expr> { ... }`):
  color:  <color>
  line:   solid | dashed | dotted
  head:   normal | none | open | diamond
  tail:   normal | none | open | diamond
"""

# ---------------------------------------------------------------------------
# Full schema text for AI prompts
# ---------------------------------------------------------------------------

_SCHEMA_TEXT: str | None = None


def get_dsl_schema_text() -> str:
    """Return a formatted reference string covering the full LikeC4 DSL.

    Used to build the AI system prompt and can be embedded in API docs.
    The string is computed once and cached.
    """
    global _SCHEMA_TEXT
    if _SCHEMA_TEXT is None:
        sections = [
            "# LikeC4 DSL Reference",
            _TOP_LEVEL.strip(),
            _SPECIFICATION.strip(),
            _MODEL_ELEMENTS.strip(),
            _MODEL_RELATIONS.strip(),
            _EXTEND_ELEMENT.strip(),
            _VIEWS.strip(),
            _DEPLOYMENT.strip(),
            _GLOBALS.strip(),
            _IMPORTS.strip(),
            _STRINGS_AND_COMMENTS.strip(),
            _STYLE_PROPERTIES.strip(),
        ]
        _SCHEMA_TEXT = "\n\n---\n\n".join(sections)
    return _SCHEMA_TEXT
