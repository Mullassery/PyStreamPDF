.PHONY: dev build release test bench clean fmt check clippy

dev:
	maturin develop

build:
	maturin build

release:
	maturin build --release

test:
	cargo test && pytest tests/

bench:
	pytest tests/test_benchmark.py -v

clean:
	cargo clean
	rm -rf target dist *.egg-info

fmt:
	cargo fmt --all
	black python/ tests/

check:
	cargo check --all && cargo clippy -- -D warnings

clippy:
	cargo clippy --all -- -D warnings
