# Controllers

This package contains pure workflow helpers that should not import or depend on
Tkinter widgets.

The intended migration path is:

1. Read GUI variables on the main thread.
2. Convert them into immutable controller/config objects.
3. Pass those objects into background workers.
4. Send UI updates back through `root.after(...)`.

This keeps the GUI as a composition and routing layer instead of letting it grow
into another monolithic workflow object.
