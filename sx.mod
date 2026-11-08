entry "main.sx"
version "v0.0.3"
spectre_version "v0.0.15"

build release {
    flags "-alt -release -dynamic -inc-path:/usr/include/SDL2"
    output "./cubedoom"
}

build dev {
    flags "-alt -dynamic -inc-path:/usr/include/SDL2"
    output "./cubedoom-dev"
}

build alt {
    flags "-alt -dynamic -inc-path:/usr/include/SDL2"
    output "./cubedoom-alt"
}
