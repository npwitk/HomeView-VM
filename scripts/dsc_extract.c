// Extract every dylib from a dyld shared cache with Xcode's dsc_extractor.bundle.
// usage: dsc_extract <dsc_extractor.bundle> <cache> <out-dir>
#include <dlfcn.h>
#include <stdio.h>

typedef int (*extract_fn)(const char *cache, const char *dir, void (^progress)(unsigned, unsigned));

int main(int argc, const char *argv[]) {
    if (argc != 4) { fprintf(stderr, "usage: %s <bundle> <cache> <out-dir>\n", argv[0]); return 2; }
    void *bundle = dlopen(argv[1], RTLD_NOW);
    if (!bundle) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
    extract_fn extract = (extract_fn)dlsym(bundle, "dyld_shared_cache_extract_dylibs_progress");
    if (!extract) { fprintf(stderr, "dlsym: %s\n", dlerror()); return 1; }
    int rc = extract(argv[2], argv[3], ^(unsigned c, unsigned t) { if (c % 200 == 0) fprintf(stderr, "%u/%u\n", c, t); });
    fprintf(stderr, "rc=%d\n", rc);
    return rc;
}
