
def main():

    resources = {
                "requests.cpu": 20,
                "limits.cpu": 20,
                "requests.memory": 10,
                "limits.memory": 10
            }
    
    body={
        "spec": {
                "hard": {
                            **resources
                        }
                    }
                },

    print(f"Resources: {resources}")
    print("Resources pointers:", {**resources})
    print("Body:", body)


if __name__ == "__main__":

    # Run the main function
    main()