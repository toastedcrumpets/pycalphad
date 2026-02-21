{
  inputs = {
    # We use an out of date nixpkgs, as we need an old symengine (<0.14) for pycalphad
    nixpkgs.url = github:NixOS/nixpkgs/nixos-25.11;
    flake-utils.url = github:numtide/flake-utils;
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };


        runtype = pkgs.python3Packages.buildPythonPackage rec {
          format = "pyproject";
          name = "runtype";
          src = pkgs.fetchFromGitHub {
            owner = "erezsh";
            repo = "runtype";
            rev = "0.5.3";
            sha256 = "sha256-HGYQsunqewuxmdj9kaRZDZxUOf6hRqBySCq4bdxQ3v4=";
          };
          version = "0.5.3";
          buildInputs = with pkgs.python3.pkgs; [
            python
            poetry-core
          ];
        };

        mypython = pkgs.python3.withPackages (ps: with ps; [
          uv
          pip
          setuptools
          cython
          setuptools-scm
          numpy
          scipy
          symengine
          pandas
          pint
          matplotlib
          pyparsing
          pytest
          pytest-cov
          tinydb
          xarray
          runtype
        ]);

      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [ mypython ];
          shellHook = ''
            echo ${pkgs.lib.getExe mypython}
          '';
        };
      })
  ;
}
