import argparse
import os
import logging
from src.counter import BagCounter
from src.utils import setup_logging, load_config

def main():
    parser = argparse.ArgumentParser(description="AI-BagCounter: Automatic sack counting using YOLOv8 + ByteTrack")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--config", type=str, default="config/default_config.yaml", help="Path to config YAML")
    parser.add_argument("--line", type=float, help="Override line position (0.0 - 1.0)")
    parser.add_argument("--conf", type=float, help="Override confidence threshold")
    parser.add_argument("--direction", type=str, choices=["left_to_right", "right_to_left", "both"], help="Override count direction")
    parser.add_argument("--model", type=str, help="Override YOLO model path")
    parser.add_argument("--show", action="store_true", help="Show live preview")
    parser.add_argument("--save", action="store_true", default=True, help="Save output video")
    parser.add_argument("--output-dir", type=str, help="Override output directory")

    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)

    # Load config
    config = load_config(args.config)
    
    # Overrides
    if args.line is not None:
        config['line_position'] = args.line
    if args.conf is not None:
        config['confidence'] = args.conf
    if args.direction is not None:
        config['count_direction'] = args.direction
    if args.model is not None:
        config['model'] = args.model
    if args.show:
        config['show_preview'] = True
    if args.output_dir:
        config['output_dir'] = args.output_dir

    # Output path
    video_name = os.path.basename(args.video)
    output_path = os.path.join(config.get('output_dir', 'outputs'), f"annotated_{video_name}")

    logger.info(f"Starting BagCounter on {args.video}")
    counter = BagCounter(config)
    results = counter.process_video(args.video, output_path if args.save else None)
    
    print("-" * 30)
    print(f"Final Count for {video_name}:")
    print(f"IN:    {results['in']}")
    print(f"OUT:   {results['out']}")
    print(f"TOTAL: {results['in'] + results['out']}")
    print("-" * 30)

if __name__ == "__main__":
    main()
