{
  description = "A Python implementation of the UVM using cocotb";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  }; # inputs

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          name = "pyuvm-dev-shell";
          packages = [
            #
            # simulators
            #
            pkgs.ghdl
            pkgs.verilator
            #
            # yosys
            #
            pkgs.yosys
            pkgs.yosys-ghdl
            pkgs.yosys-synlig
            pkgs.netlistsvg
            pkgs.mcy
            pkgs.sby
            pkgs.z3
            #
            # Waveform viewers
            #
            pkgs.gtkwave
            pkgs.surfer
            #
            # Misc
            #
            pkgs.gnumake
            pkgs.git
            #
            # Python tools
            #
            pkgs.python313
            pkgs.poetry
            pkgs.pyright
            pkgs.mypy
            pkgs.black
            pkgs.ruff
          ];

          shellHook = ''
            export PROJECT_PATH=$(pwd)
            export PYTHONPATH="${self}/src:${pkgs.python313.sitePackages}"

            echo "Initializing UPVM development environment..."
            echo "Using Python version: ${pkgs.python313.version}"
            echo ""

            eval $(poetry env activate)
          '';

        }; # devShells.default = pkgs.mkShell
      } # flake-utils.lib.eachDefaultSystem
    ); # outputs
}
