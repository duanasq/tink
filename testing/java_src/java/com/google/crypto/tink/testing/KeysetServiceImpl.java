// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////

package com.google.crypto.tink.testing;

import com.google.crypto.tink.BinaryKeysetReader;
import com.google.crypto.tink.BinaryKeysetWriter;
import com.google.crypto.tink.CleartextKeysetHandle;
import com.google.crypto.tink.KeyTemplate;
import com.google.crypto.tink.KeysetHandle;
import com.google.crypto.tink.proto.Keyset;
import com.google.crypto.tink.proto.OutputPrefixType;
import com.google.crypto.tink.proto.testing.KeysetGenerateRequest;
import com.google.crypto.tink.proto.testing.KeysetGenerateResponse;
import com.google.crypto.tink.proto.testing.KeysetGrpc.KeysetImplBase;
import com.google.crypto.tink.proto.testing.KeysetPublicRequest;
import com.google.crypto.tink.proto.testing.KeysetPublicResponse;
import com.google.protobuf.ByteString;
import com.google.protobuf.ExtensionRegistryLite;
import com.google.protobuf.InvalidProtocolBufferException;
import io.grpc.Status;
import io.grpc.stub.StreamObserver;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.security.GeneralSecurityException;

/** Implement a gRPC Keyset Testing service. */
public final class KeysetServiceImpl extends KeysetImplBase {

  public KeysetServiceImpl() throws GeneralSecurityException {
  }

  @Override
  public void generate(
      KeysetGenerateRequest request, StreamObserver<KeysetGenerateResponse> responseObserver) {
    KeysetGenerateResponse response;
    try {
      com.google.crypto.tink.proto.KeyTemplate protoTemplate =
          com.google.crypto.tink.proto.KeyTemplate.parseFrom(
              request.getTemplate(), ExtensionRegistryLite.getEmptyRegistry());
      KeyTemplate template =
          KeyTemplate.create(
              protoTemplate.getTypeUrl(),
              protoTemplate.getValue().toByteArray(),
              convertOutputPrefixTypeFromProto(protoTemplate.getOutputPrefixType()));
      KeysetHandle keysetHandle = KeysetHandle.generateNew(template);
      Keyset keyset = CleartextKeysetHandle.getKeyset(keysetHandle);
      ByteArrayOutputStream keysetStream = new ByteArrayOutputStream();
      BinaryKeysetWriter.withOutputStream(keysetStream).write(keyset);
      keysetStream.close();
      response =
          KeysetGenerateResponse.newBuilder()
              .setKeyset(ByteString.copyFrom(keysetStream.toByteArray()))
              .build();
    } catch (GeneralSecurityException | InvalidProtocolBufferException e) {
      response = KeysetGenerateResponse.newBuilder().setErr(e.toString()).build();
    } catch (IOException e) {
      responseObserver.onError(Status.UNKNOWN.withDescription(e.getMessage()).asException());
      return;
    }
    responseObserver.onNext(response);
    responseObserver.onCompleted();
  }

  @Override
  public void public_(
      KeysetPublicRequest request, StreamObserver<KeysetPublicResponse> responseObserver) {
    KeysetPublicResponse response;
    try {
      KeysetHandle privateKeysetHandle =
          CleartextKeysetHandle.read(
              BinaryKeysetReader.withBytes(request.getPrivateKeyset().toByteArray()));
      KeysetHandle publicKeysetHandle = privateKeysetHandle.getPublicKeysetHandle();
      Keyset publicKeyset = CleartextKeysetHandle.getKeyset(publicKeysetHandle);
      ByteArrayOutputStream publicKeysetStream = new ByteArrayOutputStream();
      BinaryKeysetWriter.withOutputStream(publicKeysetStream).write(publicKeyset);
      publicKeysetStream.close();
      response =
          KeysetPublicResponse.newBuilder()
              .setPublicKeyset(ByteString.copyFrom(publicKeysetStream.toByteArray()))
              .build();
    } catch (GeneralSecurityException | InvalidProtocolBufferException e)  {
      response = KeysetPublicResponse.newBuilder().setErr(e.toString()).build();
    } catch (IOException e) {
      responseObserver.onError(Status.UNKNOWN.withDescription(e.getMessage()).asException());
      return;
    }
    responseObserver.onNext(response);
    responseObserver.onCompleted();
  }

  private static KeyTemplate.OutputPrefixType convertOutputPrefixTypeFromProto(
      OutputPrefixType outputPrefixType) {
    switch (outputPrefixType) {
      case TINK:
        return KeyTemplate.OutputPrefixType.TINK;
      case LEGACY:
        return KeyTemplate.OutputPrefixType.LEGACY;
      case RAW:
        return KeyTemplate.OutputPrefixType.RAW;
      case CRUNCHY:
        return KeyTemplate.OutputPrefixType.CRUNCHY;
      default:
        throw new IllegalArgumentException("Unknown output prefix type");
    }
  }
}
