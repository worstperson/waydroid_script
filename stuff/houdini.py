import os
import re
import shutil
from stuff.general import General
from tools.logger import Logger
from tools.helper import run

class Houdini(General):
    id = "libhoudini"
    partition = "system"
    dl_links = {
        "11": ["https://github.com/supremegamers/vendor_intel_proprietary_houdini/archive/81f2a51ef539a35aead396ab7fce2adf89f46e88.zip", "fbff756612b4144797fbc99eadcb6653"],
        "13": ["https://github.com/rote66/vendor_intel_proprietary_houdini/archive/740353bf4391969902bc80ee2a9258db18481b45.zip", "d4824c0c00e8fa9611e1db5124ec61f9"]
    }
    act_md5 = ...
    dl_link = ...
    dl_file_name = "libhoudini.zip"
    extract_to = "/tmp/houdiniunpack"
    init_rc_component = """
on early-init
    mount binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc

on property:ro.enable.native.bridge.exec=1
    copy /system/etc/binfmt_misc/arm_exe /proc/sys/fs/binfmt_misc/register
    copy /system/etc/binfmt_misc/arm_dyn /proc/sys/fs/binfmt_misc/register

on property:ro.enable.native.bridge.exec64=1
    copy /system/etc/binfmt_misc/arm64_exe /proc/sys/fs/binfmt_misc/register
    copy /system/etc/binfmt_misc/arm64_dyn /proc/sys/fs/binfmt_misc/register

on property:sys.boot_completed=1
    exec -- /system/bin/sh -c "echo ':arm_exe:M::\\\\x7f\\\\x45\\\\x4c\\\\x46\\\\x01\\\\x01\\\\x01\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x02\\\\x00\\\\x28::/system/bin/houdini:P' > /proc/sys/fs/binfmt_misc/register"
    exec -- /system/bin/sh -c "echo ':arm_dyn:M::\\\\x7f\\\\x45\\\\x4c\\\\x46\\\\x01\\\\x01\\\\x01\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x03\\\\x00\\\\x28::/system/bin/houdini:P' >> /proc/sys/fs/binfmt_misc/register"
    exec -- /system/bin/sh -c "echo ':arm64_exe:M::\\\\x7f\\\\x45\\\\x4c\\\\x46\\\\x02\\\\x01\\\\x01\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x02\\\\x00\\\\xb7::/system/bin/houdini64:P' >> /proc/sys/fs/binfmt_misc/register"
    exec -- /system/bin/sh -c "echo ':arm64_dyn:M::\\\\x7f\\\\x45\\\\x4c\\\\x46\\\\x02\\\\x01\\\\x01\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x03\\\\x00\\\\xb7::/system/bin/houdini64:P' >> /proc/sys/fs/binfmt_misc/register"
"""
    apply_props = {
        "ro.product.cpu.abilist": "x86_64,x86,arm64-v8a,armeabi-v7a,armeabi",
        "ro.product.cpu.abilist32": "x86,armeabi-v7a,armeabi",
        "ro.product.cpu.abilist64": "x86_64,arm64-v8a",
        "ro.dalvik.vm.native.bridge": "libhoudini.so",
        "ro.enable.native.bridge.exec": "1",
        "ro.dalvik.vm.isa.arm": "x86",
        "ro.dalvik.vm.isa.arm64": "x86_64"
    }
    files = [
        "bin/arm",
        "bin/arm64",
        "bin/houdini",
        "bin/houdini64",
        "etc/binfmt_misc",
        "etc/init/houdini.rc",
        "lib/arm",
        "lib/libhoudini.so",
        "lib64/arm64",
        "lib64/libhoudini.so"
    ]
    init = """--- org/init.rc	2024-12-28 00:40:55.154387888 -0600
+++ patch/init.rc	2024-12-27 19:23:03.446742924 -0600
@@ -977,6 +977,10 @@
     wait_for_prop apexd.status activated
     perform_apex_config

+    # Patch ld.config after apexd
+    exec -- /system/bin/sh -c "/system/bin/patch /linkerconfig/ld.config.txt < /system/etc/ld_config.patch"
+    exec -- /system/bin/sh -c "/system/bin/patch /linkerconfig/com.android.media.swcodec/ld.config.txt < /system/etc/ld_config_swcodec.patch"
+
     # Special-case /data/media/obb per b/64566063
     mkdir /data/media 0770 media_rw media_rw encryption=None
     exec - media_rw media_rw -- /system/bin/chattr +F /data/media"""
    ld_config = """--- org/ld.config.txt	2024-12-27 19:48:40.406513097 -0600
+++ patch/ld.config.txt	2024-12-27 20:28:21.597099382 -0600
@@ -58,7 +58,13 @@
 namespace.default.permitted.paths += /data
 namespace.default.permitted.paths += /mnt/expand
 namespace.default.permitted.paths += /apex/com.android.runtime/${LIB}/bionic
+namespace.default.permitted.paths += /apex/com.android.art/${LIB}
 namespace.default.permitted.paths += /system/${LIB}/bootstrap
+namespace.default.permitted.paths += /system/${LIB}
+namespace.default.permitted.paths += /system/${LIB}/arm
+namespace.default.permitted.paths += /system/${LIB}/arm/nb
+namespace.default.permitted.paths += /system/${LIB}/arm64
+namespace.default.permitted.paths += /system/${LIB}/arm64/nb
 namespace.default.permitted.paths += /system/product/${LIB}
 namespace.default.asan.search.paths = /data/asan/system/${LIB}
 namespace.default.asan.search.paths += /system/${LIB}
@@ -117,8 +123,14 @@
 namespace.default.asan.permitted.paths += /data/asan/mnt/expand
 namespace.default.asan.permitted.paths += /mnt/expand
 namespace.default.asan.permitted.paths += /apex/com.android.runtime/${LIB}/bionic
+namespace.default.asan.permitted.paths += /apex/com.android.art/${LIB}
 namespace.default.asan.permitted.paths += /data/asan/system/${LIB}/bootstrap
 namespace.default.asan.permitted.paths += /system/${LIB}/bootstrap
+namespace.default.asan.permitted.paths += /system/${LIB}
+namespace.default.asan.permitted.paths += /system/${LIB}/arm
+namespace.default.asan.permitted.paths += /system/${LIB}/arm/nb
+namespace.default.asan.permitted.paths += /system/${LIB}/arm64
+namespace.default.asan.permitted.paths += /system/${LIB}/arm64/nb
 namespace.default.asan.permitted.paths += /data/asan/system/product/${LIB}
 namespace.default.asan.permitted.paths += /system/product/${LIB}
 namespace.default.links = com_android_adbd,com_android_i18n,default,com_android_art,com_android_resolv,com_android_tethering,com_android_neuralnetworks,com_android_os_statsd
@@ -514,11 +526,17 @@
 namespace.sphal.search.paths += /vendor_extra/${LIB}
 namespace.sphal.search.paths += /vendor_extra/${LIB}/egl
 namespace.sphal.search.paths += /vendor_extra/${LIB}/hw
+namespace.sphal.search.paths += /system/${LIB}/arm
+namespace.sphal.search.paths += /system/${LIB}/arm/nb
+namespace.sphal.search.paths += /system/${LIB}/arm64
+namespace.sphal.search.paths += /system/${LIB}/arm64/nb
 namespace.sphal.permitted.paths = /odm/${LIB}
 namespace.sphal.permitted.paths += /odm_extra/${LIB}
 namespace.sphal.permitted.paths += /vendor/${LIB}
 namespace.sphal.permitted.paths += /vendor_extra/${LIB}
 namespace.sphal.permitted.paths += /system/vendor/${LIB}
+namespace.sphal.permitted.paths += /system/${LIB}/arm
+namespace.sphal.permitted.paths += /system/${LIB}/arm64
 namespace.sphal.asan.search.paths = /data/asan/odm/${LIB}
 namespace.sphal.asan.search.paths += /odm/${LIB}
 namespace.sphal.asan.search.paths += /data/asan/odm_extra/${LIB}
@@ -529,6 +547,14 @@
 namespace.sphal.asan.search.paths += /vendor/${LIB}/egl
 namespace.sphal.asan.search.paths += /data/asan/vendor/${LIB}/hw
 namespace.sphal.asan.search.paths += /vendor/${LIB}/hw
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm
+namespace.sphal.asan.search.paths += /system/${LIB}/arm
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm/nb
+namespace.sphal.asan.search.paths += /system/${LIB}/arm/nb
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm64
+namespace.sphal.asan.search.paths += /system/${LIB}/arm64
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm64/nb
+namespace.sphal.asan.search.paths += /system/${LIB}/arm64/nb
 namespace.sphal.asan.search.paths += /data/asan/vendor_extra/${LIB}
 namespace.sphal.asan.search.paths += /vendor_extra/${LIB}
 namespace.sphal.asan.search.paths += /data/asan/vendor_extra/${LIB}/egl
@@ -545,6 +571,10 @@
 namespace.sphal.asan.permitted.paths += /vendor_extra/${LIB}
 namespace.sphal.asan.permitted.paths += /data/asan/system/vendor/${LIB}
 namespace.sphal.asan.permitted.paths += /system/vendor/${LIB}
+namespace.sphal.asan.permitted.paths += /data/asan/system/${LIB}/arm
+namespace.sphal.asan.permitted.paths += /system/${LIB}/arm
+namespace.sphal.asan.permitted.paths += /data/asan/system/${LIB}/arm64
+namespace.sphal.asan.permitted.paths += /system/${LIB}/arm64
 namespace.sphal.links = rs,default,vndk,com_android_neuralnetworks
 namespace.sphal.link.rs.shared_libs = libRS_internal.so
 namespace.sphal.link.default.shared_libs = libEGL.so:libGLESv1_CM.so:libGLESv2.so:libGLESv3.so:libRS.so:libandroid_net.so:libbinder_ndk.so:libc.so:libcgrouprc.so:libclang_rt.asan-i686-android.so:libclang_rt.asan-x86_64-android.so:libdl.so:liblog.so:libm.so:libmediandk.so:libnativewindow.so:libneuralnetworks.so:libselinux.so:libsync.so:libvndksupport.so:libvulkan.so
@@ -1560,11 +1590,17 @@
 namespace.sphal.search.paths += /vendor_extra/${LIB}
 namespace.sphal.search.paths += /vendor_extra/${LIB}/egl
 namespace.sphal.search.paths += /vendor_extra/${LIB}/hw
+namespace.sphal.search.paths += /system/${LIB}/arm
+namespace.sphal.search.paths += /system/${LIB}/arm/nb
+namespace.sphal.search.paths += /system/${LIB}/arm64
+namespace.sphal.search.paths += /system/${LIB}/arm64/nb
 namespace.sphal.permitted.paths = /odm/${LIB}
 namespace.sphal.permitted.paths += /odm_extra/${LIB}
 namespace.sphal.permitted.paths += /vendor/${LIB}
 namespace.sphal.permitted.paths += /vendor_extra/${LIB}
 namespace.sphal.permitted.paths += /system/vendor/${LIB}
+namespace.sphal.permitted.paths += /system/${LIB}/arm
+namespace.sphal.permitted.paths += /system/${LIB}/arm64
 namespace.sphal.asan.search.paths = /data/asan/odm/${LIB}
 namespace.sphal.asan.search.paths += /odm/${LIB}
 namespace.sphal.asan.search.paths += /data/asan/odm_extra/${LIB}
@@ -1581,6 +1617,14 @@
 namespace.sphal.asan.search.paths += /vendor_extra/${LIB}/egl
 namespace.sphal.asan.search.paths += /data/asan/vendor_extra/${LIB}/hw
 namespace.sphal.asan.search.paths += /vendor_extra/${LIB}/hw
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm
+namespace.sphal.asan.search.paths += /system/${LIB}/arm
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm/nb
+namespace.sphal.asan.search.paths += /system/${LIB}/arm/nb
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm64
+namespace.sphal.asan.search.paths += /system/${LIB}/arm64
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm/nb64
+namespace.sphal.asan.search.paths += /system/${LIB}/arm64/nb
 namespace.sphal.asan.permitted.paths = /data/asan/odm/${LIB}
 namespace.sphal.asan.permitted.paths += /odm/${LIB}
 namespace.sphal.asan.permitted.paths += /data/asan/odm_extra/${LIB}
@@ -1591,6 +1635,8 @@
 namespace.sphal.asan.permitted.paths += /vendor_extra/${LIB}
 namespace.sphal.asan.permitted.paths += /data/asan/system/vendor/${LIB}
 namespace.sphal.asan.permitted.paths += /system/vendor/${LIB}
+namespace.sphal.asan.permitted.paths += /data/asan/system/${LIB}/arm
+namespace.sphal.asan.permitted.paths += /system/${LIB}/arm
 namespace.sphal.links = rs,default,vndk,com_android_neuralnetworks
 namespace.sphal.link.rs.shared_libs = libRS_internal.so
 namespace.sphal.link.default.shared_libs = libEGL.so:libGLESv1_CM.so:libGLESv2.so:libGLESv3.so:libRS.so:libandroid_net.so:libbinder_ndk.so:libc.so:libcgrouprc.so:libclang_rt.asan-i686-android.so:libclang_rt.asan-x86_64-android.so:libdl.so:liblog.so:libm.so:libmediandk.so:libnativewindow.so:libneuralnetworks.so:libselinux.so:libsync.so:libvndksupport.so:libvulkan.so"""
    ld_config_swcodec = """--- org/ld.config.txt	2024-12-27 19:48:57.143116665 -0600
+++ patch/ld.config.txt	2024-12-27 20:35:00.820457546 -0600
@@ -246,12 +246,18 @@
 namespace.sphal.search.paths += /vendor_extra/${LIB}/egl
 namespace.sphal.search.paths += /vendor_extra/${LIB}/hw
 namespace.sphal.search.paths += /system/${LIB}
+namespace.sphal.search.paths += /system/${LIB}/arm
+namespace.sphal.search.paths += /system/${LIB}/arm/nb
+namespace.sphal.search.paths += /system/${LIB}/arm64
+namespace.sphal.search.paths += /system/${LIB}/arm64/nb
 namespace.sphal.permitted.paths = /odm/${LIB}
 namespace.sphal.permitted.paths += /odm_extra/${LIB}
 namespace.sphal.permitted.paths += /vendor/${LIB}
 namespace.sphal.permitted.paths += /vendor_extra/${LIB}
 namespace.sphal.permitted.paths += /system/vendor/${LIB}
 namespace.sphal.permitted.paths += /system/${LIB}
+namespace.sphal.permitted.paths += /system/${LIB}/arm
+namespace.sphal.permitted.paths += /system/${LIB}/arm64
 namespace.sphal.asan.search.paths = /data/asan/odm/${LIB}
 namespace.sphal.asan.search.paths += /odm/${LIB}
 namespace.sphal.asan.search.paths += /data/asan/odm_extra/${LIB}
@@ -270,6 +276,14 @@
 namespace.sphal.asan.search.paths += /vendor_extra/${LIB}/hw
 namespace.sphal.asan.search.paths += /data/asan/system/${LIB}
 namespace.sphal.asan.search.paths += /system/${LIB}
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm
+namespace.sphal.asan.search.paths += /system/${LIB}/arm
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm/nb
+namespace.sphal.asan.search.paths += /system/${LIB}/arm/nb
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm64
+namespace.sphal.asan.search.paths += /system/${LIB}/arm64
+namespace.sphal.asan.search.paths += /data/asan/system/${LIB}/arm64/nb
+namespace.sphal.asan.search.paths += /system/${LIB}/arm64/nb
 namespace.sphal.asan.permitted.paths = /data/asan/odm/${LIB}
 namespace.sphal.asan.permitted.paths += /odm/${LIB}
 namespace.sphal.asan.permitted.paths += /data/asan/odm_extra/${LIB}
@@ -282,6 +296,10 @@
 namespace.sphal.asan.permitted.paths += /system/vendor/${LIB}
 namespace.sphal.asan.permitted.paths += /data/asan/system/${LIB}
 namespace.sphal.asan.permitted.paths += /system/${LIB}
+namespace.sphal.asan.permitted.paths += /data/asan/system/${LIB}/arm
+namespace.sphal.asan.permitted.paths += /system/${LIB}/arm
+namespace.sphal.asan.permitted.paths += /data/asan/system/${LIB}/arm64
+namespace.sphal.asan.permitted.paths += /system/${LIB}/arm64
 namespace.sphal.links = system,vndk
 namespace.sphal.link.system.shared_libs = libEGL.so:libGLESv1_CM.so:libGLESv2.so:libGLESv3.so:libRS.so:libandroid_net.so:libbinder_ndk.so:libc.so:libcgrouprc.so:libclang_rt.asan-i686-android.so:libclang_rt.asan-x86_64-android.so:libdl.so:liblog.so:libm.so:libmediandk.so:libnativewindow.so:libneuralnetworks.so:libselinux.so:libsync.so:libvndksupport.so:libvulkan.so
 namespace.sphal.link.system.shared_libs += libc.so"""

    def __init__(self, android_version="11") -> None:
        super().__init__()
        self.dl_link = self.dl_links[android_version][0]
        self.act_md5 = self.dl_links[android_version][1]
        self.android_version = android_version

    def copy(self):
        Logger.info("Copying libhoudini library files ...")
        name = re.findall("([a-zA-Z0-9]+)\.zip", self.dl_link)[0]
        shutil.copytree(os.path.join(self.extract_to, "vendor_intel_proprietary_houdini-" + name,
                        "prebuilts"), os.path.join(self.copy_dir, self.partition), dirs_exist_ok=True)
        init_path = os.path.join(
            self.copy_dir, self.partition, "etc", "init", "houdini.rc")
        if not os.path.isfile(init_path):
            os.makedirs(os.path.dirname(init_path), exist_ok=True)
        with open(init_path, "w") as initfile:
            initfile.write(self.init_rc_component)
        if self.android_version == "13":
            init_patch = os.path.join(self.extract_to, "init.patch")
            with open(init_patch, "w") as pfile:
                pfile.write(self.init)
            with open(init_patch, "r") as pfile:
                initrcpath = os.path.join(self.copy_dir, self.partition, "etc", "init", "hw", "init.rc")
                if not os.path.isfile(initrcpath):
                    os.makedirs(os.path.dirname(initrcpath), exist_ok=True)
                run(["patch", os.path.join("/tmp/waydroid", self.partition, "etc", "init", "hw", "init.rc"), "-o", initrcpath], stdin=pfile)
            with open(os.path.join(self.copy_dir, self.partition, "etc", "ld_config.patch"), "w") as pfile:
                pfile.write(self.ld_config)
            with open(os.path.join(self.copy_dir, self.partition, "etc", "ld_config_swcodec.patch"), "w") as pfile:
                pfile.write(self.ld_config_swcodec)
