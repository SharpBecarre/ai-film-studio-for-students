import os
from unittest.mock import patch

import pytest

from backend.runway_video_generator import generate_moving_scene


def test_runway_generation_requires_authorization(tmp_path):
    output_path = tmp_path / "test_video.mp4"

    with patch.dict(os.environ, {}, clear=True):
        with patch(
            "backend.runway_video_generator.RunwayML"
        ) as mock_runway:
            with pytest.raises(
                PermissionError,
                match="Paid Runway generation is disabled",
            ):
                generate_moving_scene(
                    tmp_path / "test_image.png",
                    output_path,
                    "Safety test only",
                )

            mock_runway.assert_not_called()

    assert not output_path.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "authorization_value",
    ["", "false", "yes", "1", "TRUEE"],
)
def test_invalid_authorization_values_are_blocked(
    tmp_path, authorization_value
):
    with patch.dict(
        os.environ,
        {"ALLOW_RUNWAY_GENERATION": authorization_value},
    ):
        with patch(
            "backend.runway_video_generator.RunwayML"
        ) as mock_runway:
            with pytest.raises(PermissionError):
                generate_moving_scene(
                    tmp_path / "test_image.png",
                    tmp_path / "test_video.mp4",
                    "Safety test only",
                )

            mock_runway.assert_not_called()

    assert list(tmp_path.iterdir()) == []
