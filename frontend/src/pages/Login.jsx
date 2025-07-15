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
import { Link, useNavigate, Navigate } from "react-router-dom";
import useAuthStore from "../store/authStore";

function Login() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();
  const login = useAuthStore((state) => state.login);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const navigate = useNavigate();
  const toast = useToast();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (data) => {
    const success = await login(data.email, data.password);
    if (!success) {
      toast({
        title: "Login failed",
        description: "Please check your credentials and try again.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  return (
    <Container maxW="container.sm" py={10}>
      <Box p={8} borderWidth={1} borderRadius={8} boxShadow="lg">
        <VStack spacing={4} align="stretch">
          <Heading textAlign="center">Login to KnowFlow</Heading>
          <form onSubmit={handleSubmit(onSubmit)}>
            <VStack spacing={4}>
              <FormControl isInvalid={errors.email}>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  {...register("email", {
                    required: "Email is required",
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: "Invalid email address",
                    },
                  })}
                />
              </FormControl>

              <FormControl isInvalid={errors.password}>
                <FormLabel>Password</FormLabel>
                <Input
                  type="password"
                  {...register("password", {
                    required: "Password is required",
                    minLength: {
                      value: 6,
                      message: "Password must be at least 6 characters",
                    },
                  })}
                />
              </FormControl>

              <Button
                type="submit"
                colorScheme="blue"
                width="full"
                isLoading={isSubmitting}
              >
                Login
              </Button>
            </VStack>
          </form>

          <Text textAlign="center">
            Don't have an account?{" "}
            <Link to="/register">
              <Button variant="link" colorScheme="blue">
                Register
              </Button>
            </Link>
          </Text>
        </VStack>
      </Box>
    </Container>
  );
}

export default Login;
