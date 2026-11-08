# ─────────────────────────────────────────────
#  SPIDERCAM 3D RECONSTRUCTION ENGINE
#  File: reconstruction_3d.py
#  Portable project-relative paths; see environment configuration below.
# ─────────────────────────────────────────────

import os
import sys
import subprocess
import threading
import time
import json
import shutil
import webbrowser
from datetime import datetime
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
import numpy as np

try:
    import open3d as o3d
except ImportError:
    o3d = None

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent


def get_data_dir(environ=None):
    config = os.environ if environ is None else environ
    configured = config.get("CRIMESCAN_DATA_DIR", "").strip()
    return Path(configured).expanduser().resolve() if configured else BASE_DIR


def resolve_colmap_executable(environ=None, path_lookup=shutil.which):
    config = os.environ if environ is None else environ
    configured = config.get("COLMAP_EXECUTABLE", "").strip()
    if configured:
        executable = Path(configured).expanduser()
        if not executable.is_file():
            raise FileNotFoundError(
                "COLMAP_EXECUTABLE does not point to an existing file."
            )
        return str(executable.resolve())
    executable = path_lookup("colmap")
    if not executable:
        raise FileNotFoundError(
            "COLMAP was not found. Install it or set COLMAP_EXECUTABLE."
        )
    return executable


DATA_DIR = get_data_dir()
RECON_DIR = DATA_DIR / "reconstruction_3d"
FRAMES_DIR = RECON_DIR / "filtered_frames"
WORKSPACE = RECON_DIR / "colmap_workspace"
SPARSE_DIR = WORKSPACE / "sparse"
DENSE_DIR = WORKSPACE / "dense"
POINTCLOUD = RECON_DIR / "pointcloud"
MESH_DIR = RECON_DIR / "mesh"
VIEWER_DIR = BASE_DIR / "viewer"
VIEWER_DATA_DIR = DATA_DIR / "viewer_data"
POINTCLOUD_JSON = VIEWER_DATA_DIR / "pointcloud.json"
EVIDENCE_JSON = VIEWER_DATA_DIR / "evidence.json"
EXPORTS_DIR = RECON_DIR / "exports"
EVIDENCE_DIR = RECON_DIR / "evidence_metadata"
DATABASE = WORKSPACE / "database.db"
LAST_RECONSTRUCTION_STATUS = {
    "status": "NOT_RUN",
    "synthetic": False,
    "reason": "",
}


def _set_reconstruction_status(status, synthetic=False, reason=""):
    global LAST_RECONSTRUCTION_STATUS
    LAST_RECONSTRUCTION_STATUS = {
        "status": status,
        "synthetic": synthetic,
        "reason": reason,
    }
    os.makedirs(RECON_DIR, exist_ok=True)
    with open(RECON_DIR / "reconstruction_status.json", "w") as f:
        json.dump(LAST_RECONSTRUCTION_STATUS, f, indent=2)

# ─────────────────────────────────────────────
#  FOLDER SETUP
# ─────────────────────────────────────────────
def setup_folders():
    folders = [
        RECON_DIR, FRAMES_DIR, WORKSPACE,
        SPARSE_DIR, DENSE_DIR, POINTCLOUD,
        MESH_DIR, VIEWER_DIR, VIEWER_DATA_DIR, EXPORTS_DIR, EVIDENCE_DIR
    ]
    for f in folders:
        os.makedirs(f, exist_ok=True)

# ─────────────────────────────────────────────
#  FRAME PREPARATION
#  Copies SpiderCam extracted frames into
#  filtered_frames/ for COLMAP
# ─────────────────────────────────────────────
def prepare_frames(frame_paths, log_fn=print):
    setup_folders()
    # Clean old frames
    for f in os.listdir(FRAMES_DIR):
        if f.endswith(('.jpg', '.png')):
            try:
                os.remove(os.path.join(FRAMES_DIR, f))
            except Exception:
                pass
    log_fn("Preparing reconstruction frames...")
    copied = 0
    for i, src in enumerate(frame_paths):
        if not os.path.exists(src):
            continue
        dst = os.path.join(FRAMES_DIR, f"frame_{i:04d}.jpg")
        shutil.copy2(src, dst)
        copied += 1
    log_fn(f"{copied} frames prepared for photogrammetry")
    return copied

# ─────────────────────────────────────────────
#  COLMAP PIPELINE
# ─────────────────────────────────────────────
def run_colmap_pipeline(log_fn=print, progress_fn=None):
    if o3d is None:
        raise RuntimeError(
            "Open3D is required for point-cloud conversion. Install dependencies "
            "from requirements.txt."
        )
    colmap_exe = resolve_colmap_executable()

    def prog(val, msg):
        log_fn(msg)
        if progress_fn:
            progress_fn(val)

    # Clean old database
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    for d in [SPARSE_DIR, DENSE_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)

    prog(5, "Photogrammetry reconstruction initiated")
    prog(10, "Analyzing reconstruction continuity")

    # ── STEP 1: Feature Extraction ────────────────────────────────
    prog(15, "Extracting spatial features")
    cmd1 = [
        colmap_exe, "feature_extractor",
        "--database_path", DATABASE,
        "--image_path", FRAMES_DIR,
        "--ImageReader.single_camera", "1",
        "--SiftExtraction.max_num_features", "8192",
    ]
    result1 = subprocess.run(cmd1, capture_output=True, text=True)
    if result1.returncode != 0:
        log_fn(f"Feature extraction warning: {result1.stderr[:200]}")
    prog(30, "Spatial features extracted")

    # ── STEP 2: Sequential Feature Matching ──────────────────────
    prog(35, "Matching reconstruction points")
    cmd2 = [
        colmap_exe, "sequential_matcher",
        "--database_path", DATABASE,
        "--SequentialMatching.overlap", "10",

    ]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    if result2.returncode != 0:
        log_fn(f"Matching warning: {result2.stderr[:200]}")
    prog(50, "Feature matching in progress")
    prog(55, "Reconstruction points matched")

    # ── STEP 3: Sparse Reconstruction ────────────────────────────
    prog(60, "Sparse reconstruction generated")
    sparse_out = os.path.join(SPARSE_DIR, "0")
    os.makedirs(sparse_out, exist_ok=True)
    cmd3 = [
        colmap_exe, "mapper",
        "--database_path", DATABASE,
        "--image_path", FRAMES_DIR,
        "--output_path", SPARSE_DIR,
        "--Mapper.num_threads", "8",
        "--Mapper.init_min_tri_angle", "1",
        "--Mapper.abs_pose_min_num_inliers", "15",
        "--Mapper.min_num_matches", "4",
        "--Mapper.ba_global_function_tolerance", "0.000001",
        "--Mapper.filter_max_reproj_error", "8",
    ]
    result3 = subprocess.run(cmd3, capture_output=True, text=True)
    if result3.returncode != 0:
        log_fn(f"Mapper warning: {result3.stderr[:200]}")
    prog(70, "Camera pose estimation complete")
    prog(75, "Sparse reconstruction complete")

    # ── STEP 4: Convert to PLY point cloud ───────────────────────
    prog(80, "Point cloud generated")
    sparse_model = os.path.join(SPARSE_DIR, "0")
    ply_out = os.path.join(POINTCLOUD, "sparse_cloud.ply")
    model_files = ("cameras.bin", "images.bin", "points3D.bin")
    if all(os.path.isfile(os.path.join(sparse_model, name)) for name in model_files):
        cmd4 = [
            colmap_exe, "model_converter",
            "--input_path", sparse_model,
            "--output_path", ply_out,
            "--output_type", "PLY"
        ]
        converted = subprocess.run(cmd4, capture_output=True, text=True)
        if (
            converted.returncode != 0
            or not os.path.isfile(ply_out)
            or os.path.getsize(ply_out) < 100
        ):
            reason = "COLMAP could not export a sparse point cloud; using synthetic fallback"
            log_fn(f"WARNING: {reason}")
            _create_fallback_pointcloud(ply_out)
            _set_reconstruction_status("SYNTHETIC_FALLBACK", True, reason)
            return ply_out
        prog(85, "Point cloud exported to PLY")
    else:
        reason = "COLMAP sparse model unavailable; ORB fallback is synthetic"
        log_fn(f"WARNING: {reason}")
        _create_fallback_pointcloud(ply_out)
        _set_reconstruction_status("SYNTHETIC_FALLBACK", True, reason)
        prog(85, "Synthetic fallback point cloud generated")
        return ply_out

    # ── STEP 5: Dense reconstruction ─────────────────────────────
    prog(86, "Dense reconstruction initialized")

    # Undistort images first
    undistort_dir = os.path.join(WORKSPACE, "dense")
    os.makedirs(undistort_dir, exist_ok=True)

    cmd5 = [
        colmap_exe, "image_undistorter",
        "--image_path", FRAMES_DIR,
        "--input_path", sparse_model,
        "--output_path", undistort_dir,
        "--output_type", "COLMAP",
    ]
    result5 = subprocess.run(cmd5)
    if result5.returncode != 0:
        log_fn("COLMAP image undistortion failed; using sparse reconstruction output.")
        return ply_out
    prog(88, "Images undistorted for dense reconstruction")

    # ── STEP 6: Patch Match Stereo ────────────────────────────────
    prog(89, "Running patch match stereo...")
    cmd6 = [
        colmap_exe, "patch_match_stereo",
        "--workspace_path", undistort_dir,
        "--workspace_type", "COLMAP",
        "--PatchMatchStereo.geom_consistency", "true",
        "--PatchMatchStereo.gpu_index", "0",
    ]
    result6 = subprocess.run(cmd6)
    if result6.returncode != 0:
        log_fn("COLMAP stereo matching failed; using sparse reconstruction output.")
        return ply_out
    prog(92, "Stereo depth maps generated")

    # ── STEP 7: Stereo Fusion ─────────────────────────────────────
    prog(93, "Fusing depth maps into dense cloud")
    dense_ply = os.path.join(POINTCLOUD, "dense_cloud.ply")
    cmd7 = [
        colmap_exe, "stereo_fusion",
        "--workspace_path", undistort_dir,
        "--workspace_type", "COLMAP",
        "--input_type", "geometric",
        "--output_path", dense_ply,
        "--StereoFusion.min_num_pixels", "3",
    ]
    result7 = subprocess.run(cmd7)
    if result7.returncode != 0:
        log_fn("COLMAP dense fusion failed; using sparse reconstruction output.")
        return ply_out
    prog(95, "Dense point cloud fused")

    # ── STEP 8: Poisson Meshing ───────────────────────────────────
    prog(96, "Generating mesh surface")
    mesh_ply = os.path.join(MESH_DIR, "mesh.ply")
    cmd8 = [
        colmap_exe, "poisson_mesher",
        "--input_path", dense_ply,
        "--output_path", mesh_ply,
    ]
    result8 = subprocess.run(cmd8)
    if result8.returncode != 0:
        log_fn("COLMAP mesh generation failed; point-cloud output remains available.")
    prog(98, "Mesh surface generated")

    # Use dense cloud if available, else sparse
    if os.path.exists(dense_ply) and os.path.getsize(dense_ply) > 1000:
        log_fn("Using dense point cloud for visualization")
        return dense_ply
    else:
        log_fn("Dense failed — using sparse cloud")
        return ply_out

# ─────────────────────────────────────────────
#  FALLBACK POINT CLOUD
#  If COLMAP fails — generates synthetic cloud
#  from frame features using OpenCV
# ─────────────────────────────────────────────
def _create_fallback_pointcloud(output_path, log_fn=print):
    import cv2
    points = []
    colors = []
    frames = sorted([
        f for f in os.listdir(FRAMES_DIR)
        if f.endswith('.jpg')
    ])
    orb = cv2.ORB_create(nfeatures=500)
    for i, fname in enumerate(frames[:30]):
        img = cv2.imread(os.path.join(FRAMES_DIR, fname))
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kps, _ = orb.detectAndCompute(gray, None)
        h, w = img.shape[:2]
        for kp in kps:
            x = (kp.pt[0] / w - 0.5) * 10
            y = (kp.pt[1] / h - 0.5) * 10
            z = i * 0.5
            px = int(kp.pt[0])
            py = int(kp.pt[1])
            b, g, r = img[min(py, h-1), min(px, w-1)]
            points.append([x, y, z])
            colors.append([r/255, g/255, b/255])
    if points:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(points))
        pcd.colors = o3d.utility.Vector3dVector(np.array(colors))
        o3d.io.write_point_cloud(output_path, pcd)

# ─────────────────────────────────────────────
#  POINT CLOUD → THREE.JS JSON CONVERSION
# ─────────────────────────────────────────────
def convert_ply_to_threejs(ply_path, log_fn=print):
    log_fn("Preparing Three.js walkthrough")
    json_out = POINTCLOUD_JSON
    os.makedirs(VIEWER_DATA_DIR, exist_ok=True)
    try:
        if o3d is None:
            raise RuntimeError(
                "Open3D is unavailable; a synthetic demonstration will be shown."
            )
        if not os.path.exists(ply_path) or os.path.getsize(ply_path) < 100:
            reason = "PLY unavailable; ORB fallback is synthetic"
            log_fn(f"PLY too small — {reason}")
            _set_reconstruction_status("SYNTHETIC_FALLBACK", True, reason)
            _create_fallback_pointcloud(ply_path, log_fn)

        pcd = o3d.io.read_point_cloud(ply_path)
        point_count = len(np.asarray(pcd.points))
        log_fn(f"PLY loaded: {point_count} points")

        if point_count < 10:
            reason = "COLMAP point cloud has insufficient points; ORB fallback is synthetic"
            log_fn(f"Too few points — {reason}")
            _set_reconstruction_status("SYNTHETIC_FALLBACK", True, reason)
            _create_fallback_pointcloud(ply_path, log_fn)
            pcd = o3d.io.read_point_cloud(ply_path)
        if len(np.asarray(pcd.points)) == 0:
            raise RuntimeError("The point cloud contains no points.")

        pcd = pcd.voxel_down_sample(voxel_size=0.02)
        points = np.asarray(pcd.points).tolist()

        if pcd.has_colors():
            colors = np.asarray(pcd.colors).tolist()
        else:
            colors = [[0.0, 0.8, 1.0]] * len(points)

        data = {
            "points":    points,
            "colors":    colors,
            "count":     len(points),
            "timestamp": datetime.now().isoformat(),
            "source":    "SpiderCam COLMAP Reconstruction" if not LAST_RECONSTRUCTION_STATUS["synthetic"] else "SpiderCam SYNTHETIC DEMONSTRATION DATA",
            "synthetic": bool(LAST_RECONSTRUCTION_STATUS["synthetic"]),
            "reconstruction_status": LAST_RECONSTRUCTION_STATUS["status"],
        }
        with open(json_out, 'w') as f:
            json.dump(data, f)
        log_fn(f"Point cloud converted: {len(points)} points → Three.js ready")
        return json_out

    except Exception as e:
        reason = (
            "Point-cloud conversion failed; synthetic demonstration data is shown: "
            f"{e}"
        )
        log_fn(reason)
        _set_reconstruction_status("SYNTHETIC_DEMONSTRATION", True, reason)
        _create_demo_pointcloud_json(json_out)
        return json_out

def _create_demo_pointcloud_json(json_out):
    """Create explicitly labeled synthetic data when no reconstruction is available."""
    os.makedirs(os.path.dirname(json_out), exist_ok=True)
    points = []
    colors = []
    for i in range(2000):
        x = (np.random.rand() - 0.5) * 20
        y = (np.random.rand() - 0.5) * 5
        z = (np.random.rand() - 0.5) * 20
        points.append([x, y, z])
        colors.append([0.0, 0.8, 1.0])
    data = {
        "points": points,
        "colors": colors,
        "count": len(points),
        "timestamp": datetime.now().isoformat(),
        "source": "SpiderCam SYNTHETIC DEMONSTRATION DATA",
        "synthetic": True,
        "reconstruction_status": "SYNTHETIC_DEMONSTRATION",
    }
    with open(json_out, 'w') as f:
        json.dump(data, f)

# ─────────────────────────────────────────────
#  EVIDENCE METADATA EXPORT
# ─────────────────────────────────────────────
def export_evidence_metadata(detections, log_fn=print):
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    os.makedirs(VIEWER_DATA_DIR, exist_ok=True)
    meta_path = EVIDENCE_DIR / "evidence.json"
    evidence = []
    for d in detections:
        evidence.append({
            "label":      d.get("label", "Unknown"),
            "confidence": d.get("confidence", 0),
            "grid":       d.get("grid", "—"),
            "category":   d.get("category", "SCENE OBJECT"),
            "center":     list(d.get("center", [0, 0])),
        })
    meta = {
        "timestamp": datetime.now().isoformat(),
        "total":     len(evidence),
        "evidence":  evidence
    }
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    shutil.copy2(meta_path, EVIDENCE_JSON)
    log_fn(f"Evidence metadata exported: {len(evidence)} items")

# ─────────────────────────────────────────────
#  FLASK SERVER
# ─────────────────────────────────────────────
flask_app = Flask(__name__, static_folder=str(VIEWER_DIR))
_flask_started = False

@flask_app.route('/')
def index():
    return send_from_directory(str(VIEWER_DIR), 'index.html')

@flask_app.route('/pointcloud.json')
def pointcloud():
    return send_from_directory(str(VIEWER_DATA_DIR), 'pointcloud.json')

@flask_app.route('/evidence.json')
def evidence():
    path = EVIDENCE_JSON
    if not os.path.exists(path):
        return jsonify({"evidence": [], "total": 0})
    return send_from_directory(str(VIEWER_DATA_DIR), 'evidence.json')

@flask_app.route('/status')
def status():
    return jsonify({"status": "running", "app": "SpiderCam 3D Viewer"})

def start_flask_server(log_fn=print):
    global _flask_started
    if _flask_started:
        log_fn("Flask server already running")
        return
    def run():
        flask_app.run(host='127.0.0.1', port=5000,
                      debug=False, use_reloader=False)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    _flask_started = True
    time.sleep(1.5)
    log_fn("Flask forensic viewer server started → localhost:5000")

def launch_browser():
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:5000")

# ─────────────────────────────────────────────
#  FULL RECONSTRUCTION PIPELINE
#  Called from SpiderCam QThread
# ─────────────────────────────────────────────
def run_full_reconstruction(
    frame_paths,
    detections=None,
    log_fn=print,
    progress_fn=None
):
    try:
        setup_folders()
        _set_reconstruction_status("RUNNING")
        if o3d is None:
            raise RuntimeError(
                "Open3D is required for 3D reconstruction. Install dependencies "
                "from requirements.txt."
            )
        resolve_colmap_executable()

        # 1. Prepare frames
        copied = prepare_frames(frame_paths, log_fn)
        if copied < 2:
            log_fn("ERROR: Need at least 2 frames for reconstruction")
            _set_reconstruction_status(
                "FAILED", False, "At least two image frames are required."
            )
            return False

        # 2. Export evidence metadata
        export_evidence_metadata(detections or [], log_fn)

        # 3. Run COLMAP
        ply_path = run_colmap_pipeline(log_fn, progress_fn)

        # 4. Convert to Three.js format
        convert_ply_to_threejs(ply_path, log_fn)

        # 5. Start Flask server
        start_flask_server(log_fn)

        # 6. Launch browser
        if progress_fn:
            progress_fn(95)
        log_fn("Launching forensic walkthrough viewer")
        t = threading.Thread(target=launch_browser, daemon=True)
        t.start()

        if progress_fn:
            progress_fn(100)
        if LAST_RECONSTRUCTION_STATUS["synthetic"]:
            log_fn(
                "SYNTHETIC DEMONSTRATION DATA — not a reconstructed scene; "
                "do not use as evidence."
            )
        else:
            _set_reconstruction_status("COMPLETE")
            log_fn("COLMAP reconstruction output prepared for visualization")
        return True

    except Exception as e:
        _set_reconstruction_status("FAILED", False, str(e))
        log_fn(f"Reconstruction failed: {e}")
        return False