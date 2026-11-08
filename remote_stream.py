"""
SpiderCam Remote Stream — Desktop LiveKit subscriber
=====================================================

Receives the mobile SpiderCam camera stream from LiveKit Cloud and emits
decoded BGR numpy frames to the existing desktop SCS pipeline.

Pipeline:

    Android Camera
         |
         v
    LiveKit H.264 publisher
         |
         v
    LiveKit Cloud
         |
         v
    Python LiveKit subscriber
         |
         v
    RGBA VideoFrame
         |
         v
    OpenCV BGR numpy frame
         |
         v
    SpiderCam SCS

IMPORTANT:
- This module does NOT perform forensic acquisition.
- frame_ready is only the live-stream frame feed.
- Acquisition numbering remains handled by the SCS acquisition system.
"""

import asyncio
import os
import threading

import cv2
import numpy as np
import requests

from PyQt6.QtCore import QThread, pyqtSignal


# ============================================================================
# LIVEKIT IMPORT
# ============================================================================

try:
    from livekit import rtc

    LIVEKIT_AVAILABLE = True

except ImportError:
    rtc = None
    LIVEKIT_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

BACKEND_URL = os.environ.get("SPIDERCAM_API_BASE_URL", "").strip().rstrip("/")


def get_remote_config(environ=None, backend_url=None):
    """Return configured remote-stream URL and key without logging the key."""
    config = os.environ if environ is None else environ
    url = (backend_url or config.get("SPIDERCAM_API_BASE_URL", "")).strip().rstrip("/")
    shared_key = config.get("SPIDERCAM_SHARED_KEY", "").strip()
    if not url:
        raise RuntimeError("SPIDERCAM_API_BASE_URL is not configured.")
    if not shared_key:
        raise RuntimeError("SPIDERCAM_SHARED_KEY is not configured.")
    return url, shared_key


# ============================================================================
# REMOTE STREAM THREAD
# ============================================================================

class SpiderCamRemoteThread(QThread):

    # Raw/display pipeline frame.
    # Shape:
    #     H × W × 3
    # dtype:
    #     uint8
    # colour:
    #     BGR
    frame_ready = pyqtSignal(np.ndarray)

    # state, message
    state_changed = pyqtSignal(str, str)

    # Actual decoded resolution.
    resolution_ready = pyqtSignal(int, int)


    def __init__(self, device_id, case_id, backend_url=None):
        super().__init__()

        self.device_id = device_id
        self.case_id = case_id

        self.backend_url = (backend_url or BACKEND_URL).strip().rstrip("/")

        self._loop = None
        self._stop_event = None
        self._room = None
        self._video_task = None

        self._frame_count = 0
        self._invalid_frame_count = 0

        self._last_width = 0
        self._last_height = 0


    # ========================================================================
    # TOKEN
    # ========================================================================

    def _fetch_token(self):

        backend_url, shared_key = get_remote_config(
            backend_url=self.backend_url
        )

        identity = (
            f"desktop-viewer-"
            f"{os.getpid()}-"
            f"{threading.get_ident()}"
        )

        try:
            response = requests.post(
                f"{backend_url}/token",
                json={
                    "identity": identity,
                    "room": self.case_id,
                    "can_publish": False,
                    "can_subscribe": True,
                    "device_type": "VIEWER",
                },
                headers={"X-API-Key": shared_key},
                timeout=10,
            )
        except requests.RequestException:
            raise RuntimeError("Token request could not be completed.") from None

        if response.status_code != 200:
            raise RuntimeError(
                f"Token request failed "
                f"({response.status_code})."
            )

        data = response.json()

        token = data.get("token")
        url = data.get("url")

        if not token:
            raise RuntimeError(
                "Backend token response did not contain 'token'."
            )

        if not url:
            raise RuntimeError(
                "Backend token response did not contain 'url'."
            )

        return token, url


    # ========================================================================
    # QTHREAD ENTRY
    # ========================================================================

    def run(self):

        if not LIVEKIT_AVAILABLE:

            self.state_changed.emit(
                "error",
                "Python 'livekit' package is not installed. "
                "Run: pip install livekit",
            )

            return


        self._loop = asyncio.new_event_loop()

        asyncio.set_event_loop(self._loop)

        try:

            self._loop.run_until_complete(
                self._main()
            )

        except Exception as exc:

            self.state_changed.emit(
                "error",
                f"Remote stream error: {exc}",
            )

        finally:

            try:
                pending = asyncio.all_tasks(self._loop)

                for task in pending:
                    task.cancel()

            except Exception:
                pass

            self._loop.close()

            self._loop = None


    # ========================================================================
    # MAIN LIVEKIT SESSION
    # ========================================================================

    async def _main(self):

        self.state_changed.emit(
            "connecting",
            "Requesting access token…",
        )


        # --------------------------------------------------------------------
        # TOKEN
        # --------------------------------------------------------------------

        try:

            token, url = await asyncio.get_event_loop().run_in_executor(
                None,
                self._fetch_token,
            )

        except Exception as exc:

            self.state_changed.emit(
                "error",
                f"Token request failed: {exc}",
            )

            return


        # --------------------------------------------------------------------
        # ROOM
        # --------------------------------------------------------------------

        self.state_changed.emit(
            "connecting",
            "Connecting to LiveKit room…",
        )


        room = rtc.Room()

        self._room = room

        self._stop_event = asyncio.Event()

        got_video = asyncio.Event()


        # --------------------------------------------------------------------
        # TRACK SUBSCRIBED
        # --------------------------------------------------------------------

        @room.on("track_subscribed")
        def on_track_subscribed(
            track,
            publication,
            participant,
        ):

            try:

                if track.kind != rtc.TrackKind.KIND_VIDEO:
                    return


                if got_video.is_set():
                    return


                # ------------------------------------------------------------
                # Publication diagnostics
                # ------------------------------------------------------------

                publication_width = getattr(
                    publication,
                    "width",
                    None,
                )

                publication_height = getattr(
                    publication,
                    "height",
                    None,
                )

                mime_type = getattr(
                    publication,
                    "mime_type",
                    None,
                )

                quality_message = "subscriber quality request unavailable"
                try:
                    publication.set_video_quality(
                        rtc.VideoQuality.VIDEO_QUALITY_HIGH
                    )
                    quality_message = "subscriber quality HIGH requested"
                except ValueError:
                    quality_message = "track is not simulcasted; using published layer"
                except Exception as exc:
                    quality_message = f"subscriber quality request failed: {exc}"

                self.state_changed.emit(
                    "connecting",
                    (
                        f"Video track subscribed — "
                        f"publication={publication_width}×"
                        f"{publication_height}, "
                        f"codec={mime_type or 'unknown'}; "
                        f"{quality_message}"
                    ),
                )


                got_video.set()


                # Keep a reference to the task.
                # This prevents the consumer from becoming an
                # untracked background task.

                self._video_task = asyncio.create_task(
                    self._consume_video(
                        track,
                        publication,
                        participant,
                    )
                )


            except Exception as exc:

                self.state_changed.emit(
                    "error",
                    f"Track subscription error: {exc}",
                )


        # --------------------------------------------------------------------
        # DISCONNECTED
        # --------------------------------------------------------------------

        @room.on("disconnected")
        def on_disconnected(reason=None):

            if self._stop_event is None:
                return


            if not self._stop_event.is_set():

                self.state_changed.emit(
                    "error",
                    f"Disconnected from room: {reason}",
                )


            self._stop_event.set()


        # --------------------------------------------------------------------
        # CONNECT
        # --------------------------------------------------------------------

        try:

            await room.connect(
                url,
                token,
            )

        except Exception as exc:

            self.state_changed.emit(
                "error",
                f"Room connect failed: {exc}",
            )

            return


        self.state_changed.emit(
            "connecting",
            f"Waiting for {self.device_id} video track…",
        )


        # --------------------------------------------------------------------
        # WAIT FOR VIDEO
        # --------------------------------------------------------------------

        try:

            await asyncio.wait_for(
                got_video.wait(),
                timeout=15.0,
            )

        except asyncio.TimeoutError:

            self.state_changed.emit(
                "error",
                (
                    f"No video track from {self.device_id} "
                    f"within 15 seconds. "
                    f"Confirm the mobile camera is LIVE."
                ),
            )

            await self._disconnect_room()

            return


        # --------------------------------------------------------------------
        # DO NOT CLAIM LIVE BASED ONLY ON TRACK SUBSCRIPTION.
        #
        # _consume_video will validate the actual decoded frames.
        # --------------------------------------------------------------------

        self.state_changed.emit(
            "connecting",
            f"Video track received from {self.device_id} — decoding…",
        )


        # --------------------------------------------------------------------
        # KEEP SESSION ALIVE
        # --------------------------------------------------------------------

        while (
            self._stop_event is not None
            and not self._stop_event.is_set()
        ):

            await asyncio.sleep(0.2)


        await self._disconnect_room()


    # ========================================================================
    # VIDEO CONSUMER
    # ========================================================================

    async def _consume_video(
        self,
        track,
        publication=None,
        participant=None,
    ):

        """
        Explicitly request RGBA frames from LiveKit.

        The desktop pipeline ultimately requires:

            numpy uint8
            H × W × 3
            BGR
        """

        try:

            # ----------------------------------------------------------------
            # EXPLICIT VIDEO FORMAT
            # ----------------------------------------------------------------

            video_stream = rtc.VideoStream(
                track,
                format=rtc.VideoBufferType.RGBA,
                capacity=1,
            )


        except TypeError:

            # Compatibility fallback for SDK builds where the VideoStream
            # constructor does not expose the format argument.

            self.state_changed.emit(
                "connecting",
                (
                    "LiveKit VideoStream format selection unavailable; "
                    "using SDK default format."
                ),
            )

            video_stream = rtc.VideoStream(
                track,
                capacity=1,
            )


        first_valid_frame = True


        try:

            async for event in video_stream:

                if (
                    self._stop_event is not None
                    and self._stop_event.is_set()
                ):
                    break


                frame = event.frame


                # ------------------------------------------------------------
                # ACTUAL DECODED DIMENSIONS
                # ------------------------------------------------------------

                width = int(frame.width)
                height = int(frame.height)


                # ------------------------------------------------------------
                # REJECT INVALID / PLACEHOLDER FRAMES
                # ------------------------------------------------------------

                if width <= 2 or height <= 2:

                    self._invalid_frame_count += 1

                    if self._invalid_frame_count in (
                        1,
                        10,
                        30,
                        60,
                    ):

                        self.state_changed.emit(
                            "connecting",
                            (
                                f"LiveKit decoder produced "
                                f"invalid frame {width}×{height} "
                                f"(invalid "
                                f"{self._invalid_frame_count})"
                            ),
                        )

                    continue


                # ------------------------------------------------------------
                # CONVERT TO RGBA IF NECESSARY
                # ------------------------------------------------------------

                try:

                    if frame.type == rtc.VideoBufferType.RGBA:

                        rgba = frame

                    else:

                        rgba = frame.convert(
                            rtc.VideoBufferType.RGBA
                        )

                except Exception as exc:

                    self.state_changed.emit(
                        "error",
                        (
                            "LiveKit frame conversion failed: "
                            f"{exc}"
                        ),
                    )

                    continue


                width = int(rgba.width)
                height = int(rgba.height)


                # ------------------------------------------------------------
                # SECOND DIMENSION VALIDATION
                # ------------------------------------------------------------

                if width <= 2 or height <= 2:

                    self._invalid_frame_count += 1
                    continue


                # ------------------------------------------------------------
                # RAW BYTE BUFFER
                # ------------------------------------------------------------

                raw = np.frombuffer(
                    rgba.data,
                    dtype=np.uint8,
                )


                expected_bytes = (
                    width *
                    height *
                    4
                )


                if raw.size != expected_bytes:

                    self.state_changed.emit(
                        "error",
                        (
                            "Invalid RGBA frame buffer: "
                            f"{width}×{height}, "
                            f"received {raw.size} bytes, "
                            f"expected {expected_bytes}."
                        ),
                    )

                    continue


                # ------------------------------------------------------------
                # NUMPY RGBA
                # ------------------------------------------------------------

                rgba_array = raw.reshape(
                    height,
                    width,
                    4,
                )


                # ------------------------------------------------------------
                # RGBA → BGR
                # ------------------------------------------------------------

                bgr = cv2.cvtColor(
                    rgba_array,
                    cv2.COLOR_RGBA2BGR,
                )


                # ------------------------------------------------------------
                # FINAL FRAME VALIDATION
                # ------------------------------------------------------------

                if (
                    bgr.ndim != 3
                    or bgr.shape[0] != height
                    or bgr.shape[1] != width
                    or bgr.shape[2] != 3
                ):

                    self.state_changed.emit(
                        "error",
                        (
                            "Invalid BGR frame generated: "
                            f"{bgr.shape}"
                        ),
                    )

                    continue


                # ------------------------------------------------------------
                # UPDATE REAL STREAM METADATA
                # ------------------------------------------------------------

                self._frame_count += 1

                self._last_width = width
                self._last_height = height


                # ------------------------------------------------------------
                # FIRST VALID FRAME
                # ------------------------------------------------------------

                if first_valid_frame:

                    self.resolution_ready.emit(
                        width,
                        height,
                    )

                    self.state_changed.emit(
                        "live",
                        (
                            f"DESKTOP DECODE — {self.device_id} "
                            f"received={width}×{height}, channels=3"
                        ),
                    )

                    first_valid_frame = False


                # ------------------------------------------------------------
                # SEND FRAME TO EXISTING SCS PIPELINE
                # ------------------------------------------------------------

                self.frame_ready.emit(
                    bgr
                )


        except asyncio.CancelledError:

            raise


        except Exception as exc:

            self.state_changed.emit(
                "error",
                f"Video stream error: {exc}",
            )


        finally:

            try:
                await video_stream.aclose()
            except Exception:
                pass


    # ========================================================================
    # DISCONNECT
    # ========================================================================

    async def _disconnect_room(self):

        room = self._room

        self._room = None


        if room is None:
            return


        try:
            await room.disconnect()
        except Exception:
            pass


        try:
            await room.dispose()
        except Exception:
            pass


    # ========================================================================
    # STOP
    # ========================================================================

    def stop(self):

        if (
            self._loop is not None
            and self._stop_event is not None
        ):

            try:

                self._loop.call_soon_threadsafe(
                    self._stop_event.set
                )

            except Exception:
                pass


        if self._video_task is not None:

            try:

                if self._loop is not None:

                    self._loop.call_soon_threadsafe(
                        self._video_task.cancel
                    )

            except Exception:
                pass


        self.wait(5000)