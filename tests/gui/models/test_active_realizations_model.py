from tests import ErtTest

from ert_gui.ertwidgets.models.activerealizationsmodel import mask_to_rangestring


class ActiveRealizationsModelTest(ErtTest):
    def testMaskToRangeConversion(self):
        cases = (
            ([0, 1, 0, 1, 1, 1, 0], "1, 3-5"),
            ([0, 1, 0, 1, 1, 1, 1], "1, 3-6"),
            ([0, 1, 0, 1, 0, 1, 0], "1, 3, 5"),
            ([1, 1, 0, 0, 1, 1, 1, 0, 1], "0-1, 4-6, 8"),
            ([1, 1, 1, 1, 1, 1, 1], "0-6"),
            ([0, 0, 0, 0, 0, 0, 0], ""),
            ([True, False, True, True], "0, 2-3"),
            ([], ""),
        )

        def nospaces(s):
            return "".join(s.split())

        for mask, expected in cases:
            rngstr = mask_to_rangestring(mask)
            self.assertEqual(
                nospaces(rngstr),
                nospaces(expected),
                msg=(
                    "Mask {} was converted to {} which is different from the "
                    "expected range {}"
                ).format(mask, rngstr, expected),
            )
