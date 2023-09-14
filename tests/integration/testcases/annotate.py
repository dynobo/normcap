import itertools
from collections import defaultdict
from pathlib import Path

import cv2 as cv

from tests.integration.testcases.data import TestCase, testcases


def create_annotated_images() -> None:
    padding = 4
    border_size = 2
    colors = itertools.cycle(
        (
            (255, 127, 14),
            (44, 160, 44),
            (148, 103, 189),
            (140, 86, 75),
            (227, 119, 194),
            (188, 189, 34),
            (23, 190, 207),
            (214, 39, 40),
            (31, 119, 180),
        )
    )

    testcases_by_images: dict[Path, list[TestCase]] = defaultdict(list)
    for case in testcases:
        testcases_by_images[case.image_path].append(case)

    for image_path, cases in testcases_by_images.items():
        image = cv.imread(str(image_path.resolve()))
        for case in cases:
            label = case.name
            left = case.left_top[0] - border_size
            top = case.left_top[1] - border_size
            right = case.right_bottom[0] + border_size
            bottom = case.right_bottom[1] + border_size
            label_size, _ = cv.getTextSize(label, cv.FONT_HERSHEY_PLAIN, 1, 1)

            color = colors.__next__()

            cv.rectangle(image, (left, top), (right, bottom), color, border_size)
            cv.rectangle(
                image,
                (right, bottom),
                (
                    right - label_size[0] - padding * 2,
                    bottom + label_size[1] + padding * 2,
                ),
                color,
                -1,
            )
            cv.putText(
                image,
                label,
                (right - label_size[0] - padding, bottom + label_size[1] + padding),
                cv.FONT_HERSHEY_PLAIN,
                1,
                (255, 255, 255),
                1,
            )
        new_image_path = str(
            image_path.with_stem(f"{image_path.stem}_annotated").resolve()
        )
        cv.imwrite(new_image_path, image)


if __name__ == "__main__":
    create_annotated_images()
