import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Text,
  useToast,
  Container,
} from "@chakra-ui/react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";

function Register() {
  const {
    register: registerField,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();
  const register = useAuthStore((state) => state.register);
  const navigate = useNavigate();
  const toast = useToast();

  // Add this to see if the form is even being processed
  console.log("Component rendered, errors:", errors);

  const onSubmit = async (data) => {
    try {
      console.log("Form submission started", data);

      if (!data.username || !data.email || !data.password) {
        console.log("Missing required fields:", { data });
        return;
      }

      console.log("Calling register function");
      const success = await register(data.username, data.email, data.password);
      console.log("Register function returned:", success);

      if (success) {
        toast({
          title: "Registration successful",
          description: "Please login with your credentials.",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
        navigate("/login");
      } else {
        toast({
          title: "Registration failed",
          description: "Please try again with different credentials.",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error("Registration error:", error);
      toast({
        title: "Registration error",
        description: error.message || "An unexpected error occurred",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // Add this to directly test form submission
  const handleFormSubmit = (e) => {
    console.log("Form submit event triggered");
    handleSubmit(onSubmit)(e);
  };

  return (
    <Container maxW="container.sm" py={10}>
      <Box p={8} borderWidth={1} borderRadius={8} boxShadow="lg">
        <VStack spacing={4} align="stretch">
          <Heading textAlign="center">Create an Account</Heading>
          <form onSubmit={handleFormSubmit} noValidate>
            <VStack spacing={4}>
              <FormControl isInvalid={errors.username}>
                <FormLabel>Username</FormLabel>
                <Input
                  {...registerField("username", {
                    required: "Username is required",
                    minLength: {
                      value: 3,
                      message: "Username must be at least 3 characters",
                    },
                  })}
                  onFocus={() => console.log("Username field focused")}
                />
                {errors.username && (
                  <Text color="red.500">{errors.username.message}</Text>
                )}
              </FormControl>

              <FormControl isInvalid={errors.email}>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  {...registerField("email", {
                    required: "Email is required",
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: "Invalid email address",
                    },
                  })}
                  onFocus={() => console.log("Email field focused")}
                />
                {errors.email && (
                  <Text color="red.500">{errors.email.message}</Text>
                )}
              </FormControl>

              <FormControl isInvalid={errors.password}>
                <FormLabel>Password</FormLabel>
                <Input
                  type="password"
                  {...registerField("password", {
                    required: "Password is required",
                    minLength: {
                      value: 6,
                      message: "Password must be at least 6 characters",
                    },
                  })}
                  onFocus={() => console.log("Password field focused")}
                />
                {errors.password && (
                  <Text color="red.500">{errors.password.message}</Text>
                )}
              </FormControl>

              <Button
                type="submit"
                colorScheme="blue"
                width="full"
                isLoading={isSubmitting}
                onClick={() => console.log("Register button clicked")}
              >
                Register
              </Button>
            </VStack>
          </form>

          <Text textAlign="center">
            Already have an account?{" "}
            <Link to="/login">
              <Button variant="link" colorScheme="blue">
                Login
              </Button>
            </Link>
          </Text>
        </VStack>
      </Box>
    </Container>
  );
}

export default Register;
