    # Set protocol version 2 to work with Indy Node 1.4
    await pool.set_protocol_version(PROTOCOL_VERSION)

    # 1.
    print_log('\n1. Creates a new local pool ledger configuration that is used '
            'later when connecting to ledger.\n')
    await pool.create_pool_ledger_config(pool_name, pool_config)

    # 2.
    print_log('\n2. Open pool ledger and get handle from libindy\n')
    pool_handle = await pool.open_pool_ledger(pool_name, None)

    # 3.
    print_log('\n3. Creating new issuer, steward, and prover secure wallet\n')
    await wallet.create_wallet(issuer_wallet_config, wallet_credentials)
    await wallet.create_wallet(steward_wallet_config, wallet_credentials)

    # 4.
    print_log('\n4. Open wallet and get handle from libindy\n')
    issuer_wallet_handle = await wallet.open_wallet(issuer_wallet_config, wallet_credentials)
    steward_wallet_handle = await wallet.open_wallet(steward_wallet_config, wallet_credentials)

    # 5.
    print_log('\n5. Generating and storing steward DID and verkey\n')
    steward_seed = '000000000000000000000000Steward1'
    did_json = json.dumps({'seed': steward_seed})
    steward_did, steward_verkey = await did.create_and_store_my_did(steward_wallet_handle, did_json)
    print_log('Steward DID: ', steward_did)
    print_log('Steward Verkey: ', steward_verkey)

    # 6.
    print_log(
        '\n6. Generating and storing trust anchor (also issuer) DID and verkey\n')
    trust_anchor_did, trust_anchor_verkey = await did.create_and_store_my_did(issuer_wallet_handle, "{}")
    print_log('Trust anchor DID: ', trust_anchor_did)
    print_log('Trust anchor Verkey: ', trust_anchor_verkey)

    # 7.
    print_log('\n7. Building NYM request to add Trust Anchor to the ledger\n')
    nym_transaction_request = await ledger.build_nym_request(submitter_did=steward_did,
                                                            target_did=trust_anchor_did,
                                                            ver_key=trust_anchor_verkey,
                                                            alias=None,
                                                            role='TRUST_ANCHOR')
    print_log('NYM transaction request: ')
    pprint.pprint(json.loads(nym_transaction_request))

    # 8.
    print_log('\n8. Sending NYM request to the ledger\n')
    nym_transaction_response = await ledger.sign_and_submit_request(pool_handle=pool_handle,
                                                                    wallet_handle=steward_wallet_handle,
                                                                    submitter_did=steward_did,
                                                                    request_json=nym_transaction_request)
    print_log('NYM transaction response: ')
    pprint.pprint(json.loads(nym_transaction_response))

    # 9.
    print_log(
        '\n9. Build the SCHEMA request to add new schema to the ledger as a Steward\n')
    seq_no = 1
    schema = {
        'seqNo': seq_no,
        'dest': steward_did,
        'data': {
            'id': '1',
            'name': 'gvt',
            'version': '1.0',
            'ver': '1.0',
            'attrNames': ['age', 'sex', 'height', 'name']
        }
    }
    schema_data = schema['data']
    print_log('Schema data: ')
    pprint.pprint(schema_data)
    print_log('Schema: ')
    pprint.pprint(schema)
    schema_request = await ledger.build_schema_request(steward_did, json.dumps(schema_data))
    print_log('Schema request: ')
    pprint.pprint(json.loads(schema_request))

    # 10.
    print_log('\n10. Sending the SCHEMA request to the ledger\n')
    schema_response = await ledger.sign_and_submit_request(pool_handle, steward_wallet_handle, steward_did, schema_request)
    print_log('Schema response:')
    pprint.pprint(json.loads(schema_response))

    # 11.
    print_log(
        '\n11. Creating and storing CRED DEFINITION using anoncreds as Trust Anchor, for the given Schema\n')
    cred_def_tag = 'cred_def_tag'
    cred_def_type = 'CL'
    cred_def_config = json.dumps({"support_revocation": False})

    (cred_def_id, cred_def_json) = await anoncreds.issuer_create_and_store_credential_def(issuer_wallet_handle, trust_anchor_did, json.dumps(schema_data), cred_def_tag, cred_def_type, cred_def_config)
    print_log('Credential definition: ')
    pprint.pprint(json.loads(cred_def_json))
