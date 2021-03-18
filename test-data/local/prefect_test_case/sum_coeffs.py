#!/usr/bin/env python


def _load_coeffs(filename):
    with open(filename) as f:
        return [float(l.strip("\n")) for l in f.readlines()]


def write_to_file(data, file):
    with open(file, "w") as f:
        f.write("\n".join(map(str, data)))


if __name__ == "__main__":
    print("Loading coefficients from poly_0.out")
    coeffs_0 = _load_coeffs("poly_0.out")

    print("Loading coefficients from poly_1.out")
    coeffs_1 = _load_coeffs("poly_1.out")

    print("Loading coefficients from poly_2.out")
    coeffs_2 = _load_coeffs("poly_2.out")

    print("Calculating polynomial")
    map(sum, zip(coeffs_0, coeffs_1, coeffs_2))
    coeffs_sum = [a + b + c for a, b, c in zip(coeffs_0, coeffs_1, coeffs_2)]

    print("Writing output to file poly_sum.out")
    write_to_file(coeffs_sum, "poly_sum.out")
