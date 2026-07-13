// DKMA Monster — Kotlin Multiplatform module.
// The shared OEM registry + detection logic, usable from Android / iOS / JVM / JS.
// Regenerate the data with:  python3 tools/gen_kmp_registry.py
//
// This is a standard KMP library setup. Versions are placeholders you can bump.

plugins {
    kotlin("multiplatform") version "2.0.0"
    id("com.android.library") version "8.5.0"
}

group = "dev.dkma"
version = "1.0.0"

kotlin {
    androidTarget {
        compilations.all {
            kotlinOptions { jvmTarget = "17" }
        }
        publishLibraryVariants("release")
    }
    jvm()
    js(IR) {
        browser()
        nodejs()
    }
    iosX64()
    iosArm64()
    iosSimulatorArm64()

    explicitApi()

    sourceSets {
        val commonMain by getting
        val commonTest by getting {
            dependencies {
                implementation(kotlin("test"))
            }
        }
        val androidMain by getting
        val jvmMain by getting
        val jsMain by getting
        val iosMain by creating {
            dependsOn(commonMain)
        }
        val iosX64Main by getting { dependsOn(iosMain) }
        val iosArm64Main by getting { dependsOn(iosMain) }
        val iosSimulatorArm64Main by getting { dependsOn(iosMain) }
    }
}

android {
    namespace = "dkma.monster"
    compileSdk = 34
    defaultConfig { minSdk = 21 }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
