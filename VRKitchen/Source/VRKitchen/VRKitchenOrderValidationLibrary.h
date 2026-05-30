#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "VRKitchenOrderValidationLibrary.generated.h"

UCLASS()
class VRKITCHEN_API UVRKitchenOrderValidationLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Orders", meta = (DefaultToSelf = "DeliveryArea"))
	static void SubmitCurrentPlateValidated(AActor* DeliveryArea, bool& OutOk);
};
