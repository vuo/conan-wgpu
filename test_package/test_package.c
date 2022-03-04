#include <stdio.h>
#include <strings.h>
#include <wgpu.h>

void logCallback(WGPULogLevel level, const char *msg)
{
	printf("[wgpu] %s\n", msg);
}

void requestAdapterCallback(WGPURequestAdapterStatus status, WGPUAdapter adapter, const char *message, void *userdata)
{
	printf("status      : %s (%d)\n",
		status == WGPURequestAdapterStatus_Success ? "success" :
			(status == WGPURequestAdapterStatus_Unavailable ? "unavailable" :
				(status == WGPURequestAdapterStatus_Error ? "error" :
					"unknown")),
		status);

	WGPUAdapterProperties properties;
	wgpuAdapterGetProperties(adapter, &properties);
	printf("vendor      : %x\n", properties.vendorID);
	printf("device      : %x\n", properties.deviceID);
	printf("name        : %s\n", properties.name);
	// printf("driver      : %s\n", properties.driverDescription);  // invalid pointer on macOS
	printf("type        : %s (%d)\n",
		properties.adapterType == WGPUAdapterType_DiscreteGPU ? "discrete GPU" :
			(properties.adapterType == WGPUAdapterType_IntegratedGPU ? "integrated GPU" :
				(properties.adapterType == WGPUAdapterType_CPU ? "CPU" :
					"unknown")),
		properties.adapterType);
	printf("backend     : %s (%d)\n",
		properties.backendType == WGPUBackendType_Null ? "null" :
			(properties.backendType == WGPUBackendType_WebGPU ? "WebGPU" :
				(properties.backendType == WGPUBackendType_D3D11 ? "D3D11" :
					(properties.backendType == WGPUBackendType_D3D12 ? "D3D12" :
						(properties.backendType == WGPUBackendType_Metal ? "Metal" :
							(properties.backendType == WGPUBackendType_Vulkan ? "Vulkan" :
								(properties.backendType == WGPUBackendType_OpenGL ? "OpenGL" :
									(properties.backendType == WGPUBackendType_OpenGLES ? "OpenGLES" :
										"unknown"))))))),
		properties.backendType);

	if (message)
	printf("message     : %s\n", message);

	*(WGPUAdapter *)userdata = adapter;
}

int main()
{
	wgpuSetLogCallback(logCallback);
	wgpuSetLogLevel(WGPULogLevel_Trace);

	printf("wgpu version: %08x\n", wgpuGetVersion());

	WGPURequestAdapterOptions options;
	bzero(&options, sizeof(options));
	WGPUAdapter adapter;
	wgpuInstanceRequestAdapter(NULL, &options, requestAdapterCallback, &adapter);
	printf("adapter     : %p\n", adapter);

	return 0;
}
