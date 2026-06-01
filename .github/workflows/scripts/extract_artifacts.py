#!/usr/bin/env python3
import os
import zipfile
import glob
import argparse
import shutil


def is_release_file(filename: str) -> bool:
    """判断是否为发布文件"""
    if not filename.startswith('android'):
        return False
    # android...-boot-gz.img, android...-boot-lz4.img, android...-AnyKernel3.zip
    if filename.endswith('.zip') and 'AnyKernel3' in filename:
        return True
    if filename.endswith('.img') and '-boot.' in filename:
        return True
    return False


def process_artifacts(artifacts_dir: str, output_dir: str, build_results_dir: str = None):
    """从 artifact zip 中提取发布文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    for zip_name in os.listdir(artifacts_dir):
        if not zip_name.endswith('.zip'):
            continue
        
        zip_path = os.path.join(artifacts_dir, zip_name)
        
        # 检查 artifact zip 本身是否是发布文件
        if is_release_file(zip_name):
            # 直接复制整个 zip
            target = os.path.join(output_dir, zip_name)
            shutil.copy2(zip_path, target)
            print(f"复制: {zip_name}")
        else:
            # 解压并提取匹配的文件
            print(f"解压: {zip_name}")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    for member in zf.namelist():
                        if member.endswith('/') or member.startswith('__MACOSX/'):
                            continue
                        
                        filename = os.path.basename(member)
                        
                        if is_release_file(filename):
                            target = os.path.join(output_dir, filename)
                            with zf.open(member) as src, open(target, 'wb') as dst:
                                dst.write(src.read())
                            print(f"  提取: {filename}")
                        else:
                            print(f"  跳过: {filename}")
            except zipfile.BadZipFile:
                print(f"错误: 无效的 zip 文件 - {zip_name}")
            except Exception as e:
                print(f"错误: {e}")
    
    # 合并 SHA256SUMS
    if build_results_dir:
        sha256sums = []
        for txt_file in glob.glob(os.path.join(build_results_dir, '*.txt')):
            basename = os.path.basename(txt_file)
            if basename == 'status.txt':
                continue
            try:
                with open(txt_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        sha256sums.append(content)
            except Exception:
                pass
        
        if sha256sums:
            sha256_path = os.path.join(output_dir, 'SHA256SUMS.txt')
            with open(sha256_path, 'w') as f:
                f.write('\n'.join(sha256sums) + '\n')
            print(f"生成: SHA256SUMS.txt")
    
    print("完成")


def main():
    parser = argparse.ArgumentParser(description="提取发布文件")
    parser.add_argument("artifacts_dir", help="artifact 目录路径")
    parser.add_argument("output_dir", help="输出目录路径")
    parser.add_argument("--build-results", help="build-results 目录路径", default=None)
    args = parser.parse_args()
    
    process_artifacts(args.artifacts_dir, args.output_dir, args.build_results)


if __name__ == "__main__":
    main()
