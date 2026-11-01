entry "main.sx"
version "v0.0.1"
spectre_version "v0.0.12"

build release {
    flags "--release --inc-path=/usr/include/SDL2"
    output "./cubedoom"
}

build dev {
    output "./cubedoom-dev --inc-path=/usr/include/SDL2"
}

build alt {
    output "./cubedoom-dev --alt --inc-path=/usr/include/SDL2"
}
